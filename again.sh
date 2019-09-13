# docker kill replica_1
# docker kill replica_2
# docker kill replica_3
# docker kill replica_4

# docker rm replica_1
# docker rm replica_2
# docker rm replica_3
# docker rm replica_4

docker kill $(docker ps -aq)
docker rm $(docker ps -aq)

docker build -t testing .

docker run -p 8082:8080 -d --name replica_1 --net=mynet --ip=192.168.0.2 -e VIEW="192.168.0.2:8080,192.168.0.3:8080,192.168.0.4:8080,192.168.0.5:8080,192.168.0.6:8080,192.168.0.7:8080" -e IP_PORT="192.168.0.2:8080" -e S="3" testing
docker run -p 8083:8080 -d --name replica_2 --net=mynet --ip=192.168.0.3 -e VIEW="192.168.0.2:8080,192.168.0.3:8080,192.168.0.4:8080,192.168.0.5:8080,192.168.0.6:8080,192.168.0.7:8080" -e IP_PORT="192.168.0.3:8080" -e S="3" testing
docker run -p 8084:8080 -d --name replica_3 --net=mynet --ip=192.168.0.4 -e VIEW="192.168.0.2:8080,192.168.0.3:8080,192.168.0.4:8080,192.168.0.5:8080,192.168.0.6:8080,192.168.0.7:8080" -e IP_PORT="192.168.0.4:8080" -e S="3" testing
docker run -p 8085:8080 -d --name replica_4 --net=mynet --ip=192.168.0.5 -e VIEW="192.168.0.2:8080,192.168.0.3:8080,192.168.0.4:8080,192.168.0.5:8080,192.168.0.6:8080,192.168.0.7:8080" -e IP_PORT="192.168.0.5:8080" -e S="3" testing
docker run -p 8086:8080 -d --name replica_5 --net=mynet --ip=192.168.0.6 -e VIEW="192.168.0.2:8080,192.168.0.3:8080,192.168.0.4:8080,192.168.0.5:8080,192.168.0.6:8080,192.168.0.7:8080" -e IP_PORT="192.168.0.6:8080" -e S="3" testing
docker run -p 8087:8080 --name replica_6 --net=mynet --ip=192.168.0.7 -e VIEW="192.168.0.2:8080,192.168.0.3:8080,192.168.0.4:8080,192.168.0.5:8080,192.168.0.6:8080,192.168.0.7:8080" -e IP_PORT="192.168.0.7:8080" -e S="3" testing

# docker run -d --name replica_1 -p 8082:8080 -e VIEW="10.0.2.15:8082,10.0.2.15:8083" -e IP_PORT="10.0.2.15:8082" -e S="2" testing 
# docker run -d --name replica_2 -p 8083:8080 -e VIEW="10.0.2.15:8082,10.0.2.15:8083" -e IP_PORT="10.0.2.15:8083" -e S="2" testing 
# sudo docker run --name replica_1 -p 8082:8080 -e VIEW="10.0.2.15:8082,10.0.2.15:8083" -e IP_PORT="10.0.2.15:8082" testing 
# sudo docker run --name replica_2 -p 8083:8080 -e VIEW="10.0.2.15:8082,10.0.2.15:8083" -e IP_PORT="10.0.2.15:8083" testing 
# sudo docker run --name replica_3 -p 8084:8080 -e VIEW="10.0.2.15:8082,10.0.2.15:8083,10.0.2.15:8084" -e IP_PORT="10.0.2.15:8084" testing 