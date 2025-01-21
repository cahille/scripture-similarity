# Scripture Similarity Project

This project is designed to find and compare scriptures verses embeddings and cosine similarity.

### Prerequisites

- Python 3.x
- Docker

### Setup

1. **In your desired directory, clone the repository**
   ```bash
   git clone https://github.com/cahille/scripture-similarity.git
   cd scripture-similarity
   ```

2. **Create and activate a virtual environment**
   ```bash
   python3 -m venv scripture-similarity
   source scripture-similarity/bin/activate
   ```

3. **Install the required Python packages**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up the database**
    - Install and start [Docker](https://docs.docker.com/engine/install/)
    - Start PostgreSQL via docker. Note well the password and database name
   ```bash
   docker run --name scripture-similarity -e POSTGRES_USER=scripture-similarity -e POSTGRES_DB=scripture-similarity -e POSTGRES_PASSWORD=scripture-similarity -p 5432:5432 -d pgvector/pgvector:pg17 -c 'listen_addresses=*'
   ```
    - Create the database tables using `dbmate`
   ```bash
   dbmate up
   ```
    - You can check the connection and database state with
   ```bash
   docker exec -it `docker ps | grep pgvector | awk '{print $1}'` psql -U scripture-similarity
   ```

5. **Index**
    - Download the standard works (Book of Mormon, Doctrine and Covenants, Pearl of Great Price, Old and New
      Testaments)
    - Index the raw verses into the `verse` table
    - Walk through all the verses and find similar verses in the other works.
   ```bash
   python3 indexer.py --threshold 0.5 # 0.5 is the default threshold
   ```
    - This will likely take a while! Indexing the raw verses will likely take a few minutes, and finding similar verses will
      take `much` longer 😁 

6. **Verify**
    - You can verify that things are looking good
   ```bash
   docker exec -it `docker ps | grep pgvector | awk '{print $1}'` psql -U scripture-similarity
   \dt # you should see the verse and similar_verse tables
   SELECT COUNT(*) FROM verse; # at current writing this should be 41995 verses, but there might be more later 😁
   SELECT COUNT(*) FROM similar_verseverse; # this will depend on the threshold 😁
   ```
   
7. **Enjoy!**