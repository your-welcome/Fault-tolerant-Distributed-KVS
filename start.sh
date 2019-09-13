cleanup ()
{
    docker kill main
    docker kill b1
    docker kill b2
    docker kill b3
    docker kill b4
    docker rm main
    docker rm b1
    docker rm b2
    docker rm b3
    docker rm b4
    kill -s SIGTERM $!
    exit 0
}

trap cleanup SIGINT SIGTERM


docker build -t hw2 .
docker run -d --name main -e "IP=localhost" -e "PORT=8080" -p 8080:8080 hw2
mainIP="$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' main)"
echo "${mainIP}" 
docker run -d --name b1   -e "IP=localhost" -e "PORT=8080" -e "MAINIP=${mainIP}:8080"  -p 8081:8080 hw2
docker run -d --name b2   -e "IP=localhost" -e "PORT=8080" -e "MAINIP=${mainIP}:8080" -p 8082:8080 hw2
docker run -d --name b3   -e "IP=localhost" -e "PORT=8080" -e "MAINIP=${mainIP}:8080"  -p 8083:8080 hw2
docker run -d --name b4   -e "IP=localhost" -e "PORT=8080" -e "MAINIP=${mainIP}:8080"  -p 8084:8080 hw2


while [ 1 ]
do
    sleep 1
done