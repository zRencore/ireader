# 📚 Lector de PDF con Voz

Una aplicación web moderna para leer documentos PDF en voz usando síntesis de voz neural de alta calidad. Construida con Streamlit y Edge-TTS.

## ✨ Características

- **Lectura de PDF**: Extrae y procesa texto de archivos PDF digitales
- **Síntesis de voz neural**: Múltiples backends de TTS con diferentes calidades y configuraciones
- **Interfaz minimalista**: Diseño inspirado en Notion, limpio y fácil de usar
- **Múltiples voces**: +20 voces en español (España y Latinoamérica)
- **Tres backends de TTS**:
  - 🌐 **Edge-TTS** (Recomendado): Voces neuronales de Microsoft, máxima calidad, requiere internet
  - 🖥️ **Piper TTS**: Alternativa offline con buena calidad, 100% local
  - 🔊 **pyttsx3**: Voces SAPI5 del sistema, solo como emergencia

## 📋 Requisitos

- Python 3.8+
- Windows (o Linux/Mac con ajustes menores)
- Conexión a internet (para Edge-TTS)

## 🚀 Instalación

1. **Clonar el repositorio**
   ```bash
   git clone https://github.com/tuusuario/Lector_EdgeTTS.git
   cd Lector_EdgeTTS
   ```

2. **Crear entorno virtual (recomendado)**
   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```

3. **Instalar dependencias**
   ```bash
   pip install -r requirements.txt
   ```

## 💻 Uso

### Opción 1: Usar el script de inicio (Windows)
```bash
run.bat
```

### Opción 2: Ejecutar directamente
```bash
streamlit run app.py
```

La aplicación se abrirá en tu navegador en `http://localhost:8501`

## 📖 Cómo usar

1. **Cargar un PDF**: Arrastra o selecciona un archivo PDF desde la interfaz
2. **Configurar lectura**: Elige las páginas, velocidad de voz y backend de TTS
3. **Reproducir**: Haz clic en "Leer en voz alta" para escuchar el contenido

## ⚙️ Configuración

El archivo `config.toml` contiene configuraciones de Streamlit:

- **address**: Dirección del servidor (por defecto localhost)
- **port**: Puerto de la aplicación (por defecto 8501)
- **headless**: Ejecutar sin interfaz del navegador
- **gatherUsageStats**: Recolección de estadísticas (deshabilitado)

## 📦 Dependencias principales

| Paquete | Propósito |
|---------|-----------|
| streamlit | Framework UI web |
| pypdf | Extracción de texto de PDFs |
| edge-tts | Síntesis de voz neural |
| piper-tts | TTS offline (opcional) |
| soundfile | Procesamiento de audio |

Ver `requirements.txt` para la lista completa.

## 🏗️ Estructura del proyecto

```
Lector_EdgeTTS/
├── app.py              # Aplicación principal Streamlit
├── pdf_processor.py    # Módulo de extracción de PDFs
├── tts_engine.py       # Motor de síntesis de voz
├── config.toml         # Configuración de Streamlit
├── requirements.txt    # Dependencias del proyecto
├── run.bat            # Script de inicio (Windows)
└── README.md          # Este archivo
```

## 🔧 Módulos

### `app.py`
Aplicación principal con interfaz Streamlit. Maneja:
- Carga de archivos PDF
- Configuración de voz y velocidad
- Control de reproducción
- Visualización de estadísticas

### `pdf_processor.py`
Módulo de procesamiento de PDFs con funciones para:
- Extracción de texto por página
- División de texto en chunks
- Estadísticas del documento

### `tts_engine.py`
Motor de síntesis de voz que gestiona:
- Detección automática de backends disponibles
- Cambio entre diferentes motores TTS
- Generación de audio en MP3

## 🌐 Backends de TTS

### Edge-TTS (Recomendado)
- **Ventajas**: Máxima calidad, muchas voces naturales
- **Desventajas**: Requiere internet, datos enviados a servidores Microsoft
- **Voces disponibles**: +20 en español

### Piper TTS
- **Ventajas**: Totalmente offline, sin conexión requerida
- **Desventajas**: Requiere descargar modelo de voz (~300MB)
- **Configuración**: Se descarga automáticamente al usar

### pyttsx3
- **Ventajas**: Cero descargas, usa voces del sistema
- **Desventajas**: Calidad robótica, voces limitadas

## 📝 Notas

- La aplicación solo soporta PDFs con **texto nativo** (seleccionable)
- Los PDFs escaneados requieren OCR (no incluido en este proyecto)
- Edge-TTS requiere conexión a internet para funcionar
- Los archivos de audio se generan en formato MP3

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Para cambios mayores, abre un issue primero para discutir los cambios propuestos.

## 📄 Licencia

Este proyecto utiliza librerías de código abierto bajo licencias MIT y compatibles.

## ⚡ Troubleshooting

**El PDF no carga:**
- Verifica que sea un PDF con texto nativo (no escaneado)
- Intenta con otro PDF para descartar problemas del archivo

**No hay sonido:**
- Verifica tu conexión a internet (para Edge-TTS)
- Comprueba que el volumen del navegador esté activo
- Intenta cambiar de backend de TTS

**Error al instalar dependencias:**
- Asegúrate de estar en el entorno virtual
- Prueba: `pip install --upgrade pip`
- Luego reinstala: `pip install -r requirements.txt`

---

**Última actualización**: 2026-06-29
