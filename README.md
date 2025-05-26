# BrickBreakerCamera
Use Mediapipe And OpenCV to create a brick breaker game

docker build -t game_cam .

xhost +local:root   

sudo docker run -it --rm --name game_cam_container -v $(pwd):/app --device=/dev/video0 -e DISPLAY=$DISPLAY -v /tmp/.X11-unix:/tmp/.X11-unix game_cam python3 /app/main.py



Creo la imagen, le doy permiso para acceder a la camara temporalmente
y corro la imagen para usar la camara con su programa
