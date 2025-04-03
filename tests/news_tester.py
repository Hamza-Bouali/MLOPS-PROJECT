import os
from dotenv import load_dotenv
from NewsDataCollector import NewsDataCollector

load_dotenv()
# Set API key in environment or hard-code for testing (not recommended for production)
os.environ["NEWS_API_KEY"] = os.environ.get("API_KEY")

# Create collector
collector = NewsDataCollector()

# Define retail keywords relevant to your business
retail_keywords = [
    "retail supply chain", 
    "consumer electronics trends",
    "apparel industry",
    "retail inventory management"
]

# Fetch articles
articles_df = collector.fetch_articles(
    keywords=retail_keywords,
    days_back=3  # Start with a small number for testing
)

# Print summary
if not articles_df.empty:
    print(f"Found {len(articles_df)} articles")
    print("\nSample articles:")
    for idx, row in articles_df.head(3).iterrows():
        print(f"- {row['title']} ({row['keyword']})")
    
    # Save articles
    collector.save_articles(articles_df, "./data/raw/news_articles.parquet")
else:
    print("No articles found")