# news_collection_dag.py
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.models import Variable
import os
import requests
import pandas as pd
import json
from minio import Minio
from io import BytesIO
from docling.document_converter import DocumentConverter
import logging
# Default arguments for the DAG
default_args = {
    'owner': 'retail_mlops',
    'depends_on_past': False,
    'start_date': datetime(2024, 4, 2),
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# Create the DAG
dag = DAG(
    'news_api_collection',
    default_args=default_args,
    description='Daily collection of news data for retail analytics',
    schedule_interval="0 */6 * * *",  # Run every 6 hours
    catchup=False,  # Prevents backfilling past runs
    
)

# Function to fetch news articles
def fetch_news_articles(**kwargs):
    api_key = Variable.get("NEWS_API_KEY")  # Securely stored in Airflow Variables
    base_url = "https://newsapi.org/v2/everything"
    
    # Get execution date from context
    execution_date = kwargs['execution_date']
    
    # Define date range (yesterday's news)
    end_date = execution_date.strftime('%Y-%m-%d')
    start_date = (execution_date - timedelta(days=1)).strftime('%Y-%m-%d')
    
    # Define retail keywords
    retail_keywords = [
        "retail supply chain", 
        "consumer electronics trends",
        "apparel industry",
        "retail inventory management"
    ]
    
    all_articles = []

    
    
    # Fetch for each keyword
    for keyword in retail_keywords:
        params = {
            'q': keyword,
            'from': start_date,
            'to': end_date,
            'language': 'en',
            'sortBy': 'publishedAt',
            'apiKey': api_key
        }
        
        response = requests.get(base_url, params=params)
        
        if response.status_code == 200:
            data = response.json()
            articles = data.get('articles', [])
            
            # Add keyword and query metadata
            for article in articles:
                article['keyword'] = keyword
                article['query_date'] = execution_date.strftime('%Y-%m-%d')
                DC=DocumentConverter()
                source = article['url']
                try:
                    article['content_md'] = DC.convert(source, max_num_pages=5).document.export_to_markdown()
                except Exception as e:
                    article['content_md'] = f"Error converting content: {str(e)}"
                
            
            all_articles.extend(articles)
        else:
            print(f"Error fetching news for '{keyword}': {response.status_code}")
    
    # Return the collected articles
    logging.info(f"Fetched {len(all_articles)} articles")
    logging.debug(f"Articles: {all_articles[:2]}")  # log first two for a quick peek
    return all_articles

# Function to process and store articles in data lake
def store_in_data_lake(**kwargs):
    # Get the articles from the previous task
    ti = kwargs['ti']
    articles = ti.xcom_pull(task_ids='fetch_news_articles')
    print("Articles received in store_in_data_lake:", len(articles))
    
    if not articles:
        print("No articles to store")
        return
    
    # Convert to DataFrame for easier processing
    df = pd.DataFrame(articles)
    df.to_csv('articles.csv', index=False)
    
    # Extract execution date
    execution_date = kwargs['execution_date']
    date_str = execution_date.strftime('%Y-%m-%d')
    
    # Initialize MinIO client
    minio_client = Minio(
        "127.0.0.1:9000",  # Replace with your MinIO server
        access_key=Variable.get("MINIO_ACCESS_KEY"),
        secret_key=Variable.get("MINIO_SECRET_KEY"),
        secure=False  # Set to True if using HTTPS
    )
    
    # Ensure buckets exist
    news_bucket = "retail-news"
    images_bucket = "retail-images"
    
    for bucket in [news_bucket, images_bucket]:
        if not minio_client.bucket_exists(bucket):
            minio_client.make_bucket(bucket)
    
    # Store article content
    articles_json = json.dumps(articles)
    articles_data = BytesIO(articles_json.encode('utf-8'))
    articles_path = f"raw/news/{date_str}/{execution_date}/articles.json"

    os.makedirs(os.path.dirname(articles_path), exist_ok=True)
    

    
    minio_client.put_object(
        news_bucket,
        articles_path,
        articles_data,
        length=len(articles_json),
        content_type="application/json"
    )
    
    print(f"Stored {len(articles)} articles in data lake at {articles_path}")
    
    # Download and store images from articles
    image_count = 0
    for idx, article in enumerate(articles):
        if article.get('urlToImage'):
            try:
                # Download image
                img_response = requests.get(article['urlToImage'], timeout=10)
                if img_response.status_code == 200:
                    # Store image in data lake
                    img_data = BytesIO(img_response.content)
                    img_size = len(img_response.content)
                    
                    # Generate image path
                    img_path = f"raw/images/{date_str}/{execution_date}/{idx}_{article['source'].get('name','unknown')}.jpg"
                    
                    os.makedirs(os.path.dirname(img_path), exist_ok=True)
                    # Upload image to MinIO
                    minio_client.put_object(
                        images_bucket,
                        img_path,
                        img_data,
                        length=img_size,
                        content_type="image/jpeg"
                    )
                    
                    image_count += 1
            except Exception as e:
                print(f"Error downloading image {article.get('urlToImage')}: {e}")
    
    print(f"Stored {image_count} images in data lake")
    
    return f"Processed {len(articles)} articles and {image_count} images for {date_str}"

# Define the tasks
fetch_task = PythonOperator(
    task_id='fetch_news_articles',
    python_callable=fetch_news_articles,
    provide_context=True,
    dag=dag,
)

store_task = PythonOperator(
    task_id='store_in_data_lake',
    python_callable=store_in_data_lake,
    provide_context=True,
    dag=dag,
)

# Set the task dependencies
fetch_task >> store_task