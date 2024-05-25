# Descripción: Este script es un ejemplo de cómo se puede utilizar la plataforma de CrewAI para coordinar un equipo de agentes de IA para crear un libro de cuentos para niños. El proceso implica la generación de un esquema, la escritura de contenido, la generación de imágenes, el formateo del contenido y la conversión del contenido a un archivo PDF. Cada tarea se asigna a un agente específico con habilidades especializadas, y el proceso se ejecuta de forma secuencial.

# Importamos las librerías necesarias
from crewai import Agent, Task, Crew, Process
from crewai_tools import tool
from langchain_openai import ChatOpenAI
from crewai_tools.tools import FileReadTool
import os, requests, re, mdpdf, subprocess
from openai import OpenAI

# Inicializamos el modelo de OpenAI o Groq
"""
llm = ChatOpenAI(
    openai_api_base="https://api.groq.com/openai/v1", # https://api.openai.com/v1 or https://api.groq.com/openai/v1 
    openai_api_key=os.getenv("GROQ_API_KEY"), # os.getenv("OPENAI_API_KEY") or os.getenv("GROQ_API_KEY")
    model_name="Llama3-70b-8192"  #  gpt-4-turbo-preview or mixtral-8x7b-32768 
)
"""

# Alternativa para usar un servidor local de Ollama
""" 
llm = ChatOpenAI(
    openai_api_base="http://localhost:11434/v1", # https://api.openai.com/v1 or https://api.groq.com/openai/v1 
    openai_api_key="Null", # os.getenv("OPENAI_API_KEY") or os.getenv("GROQ_API_KEY")
    model_name="phi3" #  gpt-4-turbo-preview or mixtral-8x7b-32768
) 
"""
# Inicializamos el modelo de OpenAI o Groq
llm = ChatOpenAI(
    openai_api_base="https://api.openai.com/v1", # https://api.openai.com/v1 or https://api.groq.com/openai/v1 
    openai_api_key=os.getenv("OPENAI_API_KEY"), # os.getenv("OPENAI_API_KEY") or os.getenv("GROQ_API_KEY")
    model_name="gpt-3.5-turbo-0125"  #  gpt-4-turbo-preview or mixtral-8x7b-32768
)

# Definimos una herramienta para leer un archivo
file_read_tool = FileReadTool(
	file_path='template.md',
	description='Una herramienta para leer el archivo de plantilla de la historia y entender el formato de salida esperado.'
)

# Definimos una herramienta para generar una imagen
@tool
def generateimage(chapter_content_and_character_details: str) -> str:
    """
    Genera una imagen para un capítulo dado, contenido del capítulo, detalles de locación y detalles del personaje.
    Utilizando la API de generación de imágenes de OpenAI,
    la guarda en la carpeta actual y devuelve la ruta de la imagen.
    """
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    response = client.images.generate(
        model="dall-e-3",
        prompt=f"La imagen es sobre: {chapter_content_and_character_details}. Estilo: Ilustración. Crea una ilustración que incorpore una paleta de colores vívida con énfasis en tonos de azul celeste y esmeralda, realzada por toques de oro para contraste y interés visual. El estilo debería evocar el detalle intrincado y la fantasía de las ilustraciones de libros de cuentos del siglo XX, combinando realismo con elementos fantásticos para crear un sentido de asombro y encantamiento. La composición debería ser rica en textura, con una luz suave y luminosa que realce la atmósfera mágica. La atención al juego de luces y sombras agregará profundidad y dimensionalidad, invitando al espectador a sumergirse en la escena. NO incluya NINGÚN TEXTO en esta imagen. NO incluya paleta de colores en esta imagen.",
        size="1024x1024",
        quality="standard",
        n=1,
    )
    image_url = response.data[0].url
    words = chapter_content_and_character_details.split()[:5] 
    safe_words = [re.sub(r'[^a-zA-Z0-9_]', '', word) for word in words]  
    filename = "_".join(safe_words).lower() + ".png"
    filepath = os.path.join(os.getcwd(), filename)

    # Descargamos la imagen y la guardamos en el directorio actual
    image_response = requests.get(image_url)
    if image_response.status_code == 200:
        with open(filepath, 'wb') as file:
            file.write(image_response.content)
    else:
        print("Falló la descarga de la imagen.")
        return ""

    return filepath

# Definimos una herramienta para convertir un archivo Markdown a PDF
@tool
def convermarkdowntopdf(markdownfile_name: str) -> str:
    """
    Convierte un archivo Markdown a un documento PDF utilizando la aplicación de línea de comandos mdpdf.

    Args:
        markdownfile_name (str): Ruta al archivo Markdown de entrada.

    Returns:
        str: Ruta del archivo PDF generado.
    """
    output_file = os.path.splitext(markdownfile_name)[0] + '.pdf'
    
    # Convierte un archivo Markdown a un documento PDF utilizando la aplicación de línea de comandos mdpdf.
    cmd = ['mdpdf', '--output', output_file, markdownfile_name]
    
    # Ejecuta el comando en el terminal
    subprocess.run(cmd, check=True)
    
    return output_file

# Definimos los agentes que participarán en el proceso de creación del libro de cuentos para niños - El esquematizador de la historia, el escritor de la historia, el generador de imágenes, el formateador de contenido y el creador de PDF.

# Definimos el agente que se encargará de esquematizar la historia
story_outliner = Agent(
  role='Esquematizador de la Historia',
  goal='Desarrollar un esquema para un libro de cuentos para niños sobre Animales, incluyendo títulos de capítulos y personajes para 5 capítulos.',
  backstory="Un creador imaginativo que establece la base de historias cautivadoras para niños.",
  verbose=True,
  llm=llm,
  allow_delegation=False
)

# Definimos el agente que se encargará de escribir la historia
story_writer = Agent(
  role='Escritor de la Historia',
  goal='Escribir el contenido completo de la historia para todos los 5 capítulos, cada capítulo de 100 palabras, entretejido las narrativas y personajes esquematizados.',
  backstory="Un narrador talentoso que da vida al mundo y personajes esquematizados, creando relatos atractivos e imaginativos para niños.",
  verbose=True,
  llm=llm,
  allow_delegation=False
)

# Definimos el agente que se encargará de generar imágenes
image_generator = Agent(
  role='Generador de Imágenes',
  goal='Generar una imagen por capítulo a partir del contenido proporcionado por el creador de esquemas. Comenzar con el número de capítulo, contenido del capítulo, detalles del personaje, información detallada sobre la locación y elementos detallados en la ubicación donde sucede la acción. Generar un total de 5 imágenes, una por una. La salida final debe contener las 5 imágenes en formato JSON.',
  backstory="Un AI creativo especializado en narrativa visual, trayendo cada capítulo a la vida a través de imágenes imaginativas y detalladas.",
  verbose=True,
  llm=llm,
  tools=[generateimage],
  allow_delegation=False
)

# Definimos el agente que se encargará de formatear el contenido
content_formatter = Agent(
    role='Formateador de Contenido',
    goal='Formatear el contenido escrito de la historia en markdown, incluyendo imágenes al principio de cada capítulo.',
    backstory='Un formateador meticuloso que mejora la legibilidad y presentación del libro de cuentos.',
    verbose=True,
    llm=llm,
    tools=[file_read_tool],
    allow_delegation=False
)

# Definimos el agente que se encargará de convertir el archivo Markdown a PDF
markdown_to_pdf_creator = Agent(
    role='Convertidor de PDF',
    goal='Convertir el archivo Markdown en un documento PDF. story.md es el nombre del archivo Markdown.',
    backstory='Un convertidor eficiente que transforma archivos Markdown en documentos PDF profesionales.',
    verbose=True,
    llm=llm,
    tools=[convermarkdowntopdf],
    allow_delegation=False
)

# Definimos las tareas que se deben realizar para completar el proceso de creación del libro de cuentos para niños.

# Tarea 1: Crear un esquema para el libro de cuentos para niños sobre Animales, detallando los títulos de los capítulos y las descripciones de los personajes para 5 capítulos.
task_outline = Task(
    description='Crear un esquema para el libro de cuentos para niños sobre Animales, detallando los títulos de los capítulos y las descripciones de los personajes para 5 capítulos.',
    agent=story_outliner,
    expected_output='Un documento de esquema estructurado que contiene 5 títulos de capítulos, con descripciones de personajes detalladas y los puntos de trama principales para cada capítulo.'
)

# Tarea 2: Escribir el contenido completo de la historia para todos los capítulos, asegurando una narrativa cohesiva y atractiva para los niños. Cada capítulo 100 palabras. Incluir el título de la historia en la parte superior.
task_write = Task(
    description='Usando el esquema proporcionado, escribir el contenido completo de la historia para todos los capítulos, asegurando una narrativa cohesiva y atractiva para los niños. Cada capítulo 100 palabras. Incluir título de la historia en la parte superior.',
    agent=story_writer,
    expected_output='Un manuscrito completo del libro de cuentos para niños sobre Animales con 5 capítulos. Cada capítulo debe contener aproximadamente 100 palabras, siguiendo el esquema proporcionado e integrando los personajes y puntos de trama en una narrativa cohesiva.'
)

# Tarea 3: Generar 5 imágenes que capturen la esencia del libro de cuentos para niños sobre Animales, alineándose con los temas, personajes y narrativa descritos para los capítulos. Hacerlo uno por uno.
task_image_generate = Task(
    description='Generar 5 imágenes que capturen la esencia del libro de cuentos para niños sobre Animales, alineándose con los temas, personajes y narrativa descritos para los capítulos. Hacerlo uno por uno.',
    agent=image_generator,
    expected_output='Un archivo de imagen digital que representa visualmente el tema principal del libro de cuentos para niños, incorporando elementos de los personajes y puntos de trama descritos en el esquema. La imagen debe ser adecuada para su inclusión en el libro de cuentos como ilustración.',
)

# Tarea 4: Formatear el contenido de la historia en markdown, incluyendo una imagen al principio de cada capítulo.
task_format_content = Task(
    description='Formatear el contenido de la historia en markdown, incluyendo una imagen al principio de cada capítulo.',
    agent=content_formatter,
    expected_output='El contenido completo del libro de cuentos para niños formateado en markdown, con cada título de capítulo seguido de la imagen correspondiente y el contenido del capítulo.',
    context=[task_write, task_image_generate],
    output_file="story.md"
)

# Tarea 5: Convertir un archivo Markdown a un documento PDF, asegurando la preservación del formato, la estructura y las imágenes incrustadas utilizando la biblioteca mdpdf.
task_markdown_to_pdf = Task(
    description='Convertir un archivo Markdown a un documento PDF, asegurando la preservación del formato, la estructura y las imágenes incrustadas utilizando la biblioteca mdpdf.',
    agent=markdown_to_pdf_creator,
    expected_output='Un documento PDF que contiene el contenido completo del libro de cuentos para niños, con formato y estructura preservados, imágenes incrustadas y una presentación atractiva para niños.'
)

# Creamos un equipo de agentes y tareas para coordinar el proceso de creación del libro de cuentos para niños.
# El proceso se ejecutará de forma secuencial, con cada tarea asignada a un agente específico con habilidades especializadas.
crew = Crew(
  agents=[story_outliner, story_writer, image_generator, content_formatter, markdown_to_pdf_creator],
  tasks=[task_outline, task_write, task_image_generate, task_format_content, task_markdown_to_pdf],
  verbose=True,
  process=Process.sequential
)

# Iniciamos el proceso de creación del libro de cuentos para niños.
result = crew.kickoff()

# Imprimimos el resultado del proceso
print(result)