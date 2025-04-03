# MLOps Project

This project implements an MLOps pipeline for retail news analytics. It includes:
- **News Data Collection:** Fetches news articles via NewsAPI.
- **Data Transformation & Storage:** Processes and stores articles and images into a data lake using MinIO.
- **Airflow DAGs:** Orchestrates the data pipeline for periodic collection and processing.
- **Testing:** Automated tests under the `tests/` directory.

## Project Structure
- `/Mlops/airflow`: Airflow configuration (DAGs, config files).
- `/Mlops/NewsDataCollector.py`: Module to fetch and process news articles.
- `/Mlops/tests`: Contains test scripts, e.g. `news_tester.py`.
- `/Mlops/README.md`: Project documentation.

## Setup and Usage
1. **Environment Variables:**  
   Set your API keys and other secrets via environment variables or Airflow Variables.
2. **Running Airflow:**  
   Initialize and run Airflow to schedule the DAGs.
3. **Testing:**  
   Run test scripts in `/Mlops/tests` to validate functionalities.

## Requirements
```bash
python -m venv myenv 
source myenv/bin/activate
pip install -r requirements.txt

```


