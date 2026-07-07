# 📚 Lector de PDF con Voz

Una aplicación web para leer PDFs y texto escrito en voz alta usando síntesis neural de alta calidad. Construida con Streamlit y con soporte para Edge-TTS, Piper TTS y pyttsx3.

## ✨ Características

- **Dos modos de uso**: leer desde PDF o escribir texto directamente para sintetizarlo
- **Extracción de texto por páginas**: permite seleccionar rangos, revisar el contenido y editarlo antes de generar audio
- **Estadísticas del documento**: muestra páginas totales, páginas con texto, caracteres, palabras y una estimación de tiempo de lectura
- **Controles de voz**: velocidad, tono, volumen y selección de voz según el backend
- **Audio reproducible y descargable**: genera salida en MP3 o WAV y permite descargarla desde la interfaz
- **Tres backends de TTS**:
   - 🌐 **Edge-TTS** (recomendado): voces neuronales de Microsoft, máxima calidad, requiere internet
   - 🖥️ **Piper TTS**: alternativa offline con buena calidad, 100% local una vez descargada la voz
   - 🔊 **pyttsx3**: voces del sistema, útil como respaldo
- **Interfaz moderna**: diseño responsive con pestañas, barra lateral compacta y tema adaptativo claro/oscuro

## 📋 Requisitos

- Python 3.8+
- Windows (o Linux/Mac con ajustes menores)
- Conexión a internet para usar Edge-TTS y descargar voces de Piper

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

Si solo vas a usar Edge-TTS, no necesitas instalar nada adicional. Piper TTS y sus modelos se usan solo si eliges ese backend.

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

1. **Elegir el modo**: usa la pestaña de PDF para cargar y procesar un documento, o la pestaña de texto para escribir directamente
2. **Configurar la voz**: selecciona el backend, la voz y los ajustes disponibles desde la barra lateral
3. **Preparar el contenido**: en PDF, selecciona el rango de páginas y edita el texto extraído si lo necesitas
4. **Generar audio**: pulsa el botón de síntesis para escuchar el resultado en el reproductor integrado
5. **Descargar el audio**: usa el botón de descarga si quieres guardar el archivo generado

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
- Escritura de texto directo
- Configuración de voz, velocidad, tono y volumen
- Control de reproducción y descarga de audio
- Visualización de estadísticas del documento

### `pdf_processor.py`
Módulo de procesamiento de PDFs con funciones para:
- Extracción de texto por página
- División de texto en chunks
- Estadísticas del documento

### `tts_engine.py`
Motor de síntesis de voz que gestiona:
- Detección automática de backends disponibles
- Cambio entre diferentes motores TTS
- Generación de audio en MP3 y WAV

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
- Piper TTS necesita descargar una voz la primera vez que se usa
- La salida final puede ser MP3 o WAV según el backend

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Para cambios mayores, abre un issue primero para discutir los cambios propuestos.

## 📄 Licencia

Este proyecto utiliza librerías de código abierto bajo licencias MIT y compatibles.

## ⚡ Troubleshooting

**El PDF no carga:**
- Verifica que sea un PDF con texto nativo (no escaneado)
- Intenta con otro PDF para descartar problemas del archivo

**No aparece texto en una página:**
- Puede tratarse de una página solo con imágenes, diagramas o texto no extraíble
- Prueba con otro rango de páginas o con otro documento

**No hay sonido:**
- Verifica tu conexión a internet (para Edge-TTS)
- Comprueba que el volumen del navegador esté activo
- Intenta cambiar de backend de TTS

**Error al instalar dependencias:**
- Asegúrate de estar en el entorno virtual
- Prueba: `pip install --upgrade pip`
- Luego reinstala: `pip install -r requirements.txt`

---

**Última actualización**: 2026-07-07
