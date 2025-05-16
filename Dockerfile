# Usa una imagen base de Python
FROM python:3.11-slim

# Instala las dependencias necesarias
RUN apt-get update && apt-get install -y \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgl1-mesa-glx \
    libegl1-mesa \
    && rm -rf /var/lib/apt/lists/*

# Instala las librerías de Python
RUN pip install pygame mediapipe opencv-python

# Copia el archivo de tu aplicación
WORKDIR /app
COPY . /app

# Expón el puerto si es necesario (aunque para este caso no es necesario para gráficos)
EXPOSE 8000

# Ejecuta tu script de Python
CMD ["python3", "main.py"]
