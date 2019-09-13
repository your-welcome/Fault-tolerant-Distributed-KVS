docker kill $(docker ps -aq)
docker rm $(docker ps -aq)
docker build -t testing .
python hw4_test.py