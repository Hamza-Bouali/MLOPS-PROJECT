import os
import requests
from datetime import datetime, timedelta
import pandas as pd
import docling
class NewsDataCollector:
    def __init__(self, api_key=None):
        # Get API key from environment variable if not provided
        self.api_key = api_key or os.environ.get("NEWS_API_KEY")
        self.countries=['']
        if not self.api_key:
            raise ValueError("NewsAPI key is required")
        self.base_url = "https://newsapi.org/v2/everything"
    
    def fetch_articles(self, keywords, days_back=2, language="en",q=None):
        """
        Fetch news articles based on keywords
        
        Args:
            keywords (list): List of keywords/phrases to search for
            days_back (int): How many days back to search
            language (str): Language code (e.g., 'en' for English)
            
        Returns:
            pandas.DataFrame: DataFrame containing the articles
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        # Format dates for NewsAPI
        from_date = start_date.strftime('%Y-%m-%d')
        to_date = end_date.strftime('%Y-%m-%d')
        
        all_articles = []
        
        # Fetch for each keyword
        for keyword in keywords:
            params = {
                'from': from_date,
                'to': to_date,
                "q":keyword,
                'language': language,
                'sortBy': 'popularity',
                'apiKey': self.api_key
            }
            
            response = requests.get(self.base_url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                articles = data.get('articles', [])
                
                # Add keyword as metadata
                for article in articles:
                    article['keyword'] = keyword
                    article['query_date'] = datetime.now().strftime('%Y-%m-%d')
                    source = article['url']
                    converter = DocumentConverter()
                    result = converter.convert(source)
                    article['content_md']=result.document.export_to_markdown()
                
                all_articles.extend(articles)
            else:
                print(f"Error fetching news for '{keyword}': {response.status_code}")
                print(response.text)
        
        # Convert to DataFrame if articles were found
        if all_articles:
            df = pd.DataFrame(all_articles)
            return df
        else:
            return pd.DataFrame()

    def transform_data(self,df):
        return df.apply(lambda row: row['source']['name'], axis=1)
    
    def save_articles(self, df, output_path):
        """Save articles to CSV/Parquet file"""
        if df.empty:
            print("No articles to save")
            return

        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
        df['source']=self.transform_data(df)
        # Save as parquet (more efficient than CSV for nested data)
        df.to_parquet(output_path)
        print(f"Saved {len(df)} articles to {output_path}")