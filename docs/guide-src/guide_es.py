"""Contenido de la guía en español. (El código de los fragmentos queda como en el repositorio, en inglés.)"""

from common import *  # noqa: F401,F403

TOC = [
    ("1", "Qué construimos", "c1"), ("2", "El panorama general", "c2"), ("3", "Punto de partida: la revisión", "c3"),
    ("4", "Fundamentos de Python que aparecen en este código", "c4"), ("5", "El motor del sorteo", "c5"),
    ("6", "Archivos, validación y reanudación", "c6"), ("7", "Aleatoriedad, justicia y --seed", "c7"),
    ("8", "La interfaz clásica de terminal", "c8"), ("9", "Los fuegos artificiales", "c9"), ("10", "La interfaz Textual", "c10"),
    ("11", "La máquina tragamonedas", "c11"), ("12", "Pruebas (tests)", "c12"), ("13", "Decisiones técnicas en una tabla", "c13"),
    ("14", "Lo que salió mal (y lo que enseñó)", "c14"), ("15", "Ejercicios", "c15"),
    ("16", "Glosario y cómo ejecutar todo", "c16"),
]

add(f"""
<section class="cover">
  <div class="kicker">pybaq · herramientas para meetups</div>
  <h1 class="title">Cómo se construyó <code>raffle-cli</code></h1>
  <p class="subtitle">Una guía para principiantes sobre el código, los diagramas y las decisiones técnicas detrás del proyecto</p>
  <div class="coverbox">
    <p><b>Versión cubierta:</b> 0.2.0 &nbsp;·&nbsp; <b>Python:</b> 3.10+ &nbsp;·&nbsp; <b>Código:</b> {sum(loc(f.name) for f in SRC.glob('*.py'))} líneas en {len(list(SRC.glob('*.py')))} módulos, {TOTAL} pruebas</p>
    <p><b>Nota honesta:</b> el primer prototipo lo escribió Andoresu; esta versión (reestructuración, correcciones, persistencia,
    fuegos artificiales, la máquina tragamonedas en Textual, pruebas y documentación) se escribió junto con Claude, un asistente de IA.
    Esta guía es la forma de devolverte el aprendizaje: cada línea importante está explicada, cada decisión tiene una razón, y los ejercicios
    del final te piden cambiar el programa tú mismo.</p>
  </div>
  <p class="how"><b>Cómo usar esta guía.</b> Lee un capítulo y luego abre el archivo del que habla y busca el código. Ejecuta el programa.
  Cambia un número, rompe algo a propósito y lee el error. Escribir código tú mismo enseña mucho más que leerlo.
  Los fragmentos de código se muestran tal como están en el repositorio (nombres y comentarios en inglés).</p>
</section>
<section class="toc"><h2>Contenido</h2><ol>{''.join(f'<li><a href="#{a}"><span>{n}</span> {t}</a></li>' for n, t, a in TOC)}</ol></section>
""")

# 1 -------------------------------------------------------------------------
add(chapter(1, "Qué construimos", "c1"))
add("""
<p><code>raffle-cli</code> hace un sorteo en la terminal para regalos en meetups: está pensado para ser <em>visible</em>, de modo que todos
puedan ver que el sorteo es justo. Le das tres archivos (personas, premios y una configuración) y sortea los ganadores, un premio a la vez.</p>
<table class="t"><tr><th>Puedes…</th><th>Con</th></tr>
<tr><td>Crear los archivos iniciales</td><td><code>raffle-cli setup</code></td></tr>
<tr><td>Hacer el sorteo clásico (Enter para revelar cada ganador)</td><td><code>raffle-cli</code></td></tr>
<tr><td>Usarlo como una tragamonedas a pantalla completa, con soporte de mouse</td><td><code>raffle-cli --tui</code></td></tr>
<tr><td>Ver solo el cierre con fuegos artificiales</td><td><code>raffle-cli fireworks</code></td></tr>
<tr><td>Hacer un sorteo reproducible y auditable</td><td><code>--seed 7</code> (siempre se muestra una semilla en los resultados)</td></tr>
<tr><td>Elegir el orden de los premios, saltar las pausas, ejecutar sin intervención</td><td><code>--order</code>, <code>--fast</code>, <code>--yes</code></td></tr>
<tr><td>Recuperarte de una caída</td><td>los ganadores se guardan en el momento de revelarlos; vuelve a ejecutar y continúa</td></tr>
</table>
<h3>Los tres archivos</h3>
""")
add(snip("""participants_file: participants.csv
prizes_file: prizes.csv
winners_file: winners.csv
recreate_from_winners: true""", "yaml", "config.yaml"))
add(snip("""name,lastname
Ada,Lovelace
Grace,Hopper""", "text", "participants.csv"))
add(snip("""item,qty
Mechanical keyboard,1
Python mug,2""", "text", "prizes.csv"))
add("<p>El programa escribe un cuarto archivo, <code>winners.csv</code>, con las columnas <code>name,lastname,item</code>.</p>")

# 2 -------------------------------------------------------------------------
add(chapter(2, "El panorama general", "c2"))
add("""<p>El proyecto original era un solo archivo con todo mezclado: leer archivos, sortear y mostrar en pantalla. El cambio más
importante fue <b>separar esos trabajos</b>. Los programadores lo llaman <em>separación de responsabilidades</em>: cada pieza hace una sola
cosa, y puedes cambiar o probar una pieza sin tocar las demás.</p>""")
add(D.architecture())
add(f"""
<table class="t"><tr><th>Archivo</th><th>Trabajo</th><th>Líneas</th><th>Ideas de Python que verás</th></tr>
<tr><td><code>raffle.py</code></td><td>El cerebro: quién gana qué. Sin imprimir, sin archivos.</td><td>{loc('raffle.py')}</td><td>dataclasses, anotaciones de tipo, tuplas como llave de orden, <code>random.Random</code></td></tr>
<tr><td><code>files.py</code></td><td>Leer, validar y escribir los archivos CSV</td><td>{loc('files.py')}</td><td><code>csv</code>, <code>pathlib</code>, excepciones propias, codificaciones</td></tr>
<tr><td><code>config.py</code></td><td>Cargar <code>config.yaml</code>, crear los archivos iniciales</td><td>{loc('config.py')}</td><td>modelos de Pydantic, YAML, clausuras (closures)</td></tr>
<tr><td><code>cli.py</code></td><td>La puerta de entrada: opciones, conexiones, errores amigables</td><td>{loc('cli.py')}</td><td>Typer, <code>Annotated</code>, callbacks, códigos de salida</td></tr>
<tr><td><code>ui.py</code></td><td>La interfaz clásica</td><td>{loc('ui.py')}</td><td>paneles y tablas de Rich, callbacks</td></tr>
<tr><td><code>fireworks.py</code></td><td>Simulación de partículas + dibujo</td><td>{loc('fireworks.py')}</td><td>clases, física sencilla, <code>rich.live.Live</code></td></tr>
<tr><td><code>tui.py</code></td><td>Aplicación Textual a pantalla completa</td><td>{loc('tui.py')}</td><td>widgets, CSS, atajos de teclado, temporizadores, mensajes</td></tr>
<tr><td><code>slot.py</code></td><td>El widget de la tragamonedas</td><td>{loc('slot.py')}</td><td>widget propio, animación con temporizadores, eventos de mouse</td></tr>
</table>
<h3>Qué pasa cuando escribes <code>raffle-cli</code></h3>
<p>Un comando como <code>raffle-cli</code> no es magia: la herramienta de empaquetado creó un pequeño script lanzador que importa tu función y la llama.</p>
""")
add(D.entrypoint())
add(snip("""[project.scripts]
raffle-cli = "raffle_cli:main_cli"

[project.optional-dependencies]
tui = ["textual>=0.86"]""", "toml", "pyproject.toml (extracto)"))

# 3 -------------------------------------------------------------------------
add(chapter(3, "Punto de partida: la revisión", "c3"))
add("""<p>El primer paso <em>no</em> fue escribir código: fue leer el prototipo y ejecutarlo para confirmar cada sospecha.
Los errores que solo sospechas son opiniones; los que reproduces son hechos. Estos son los problemas reales que se encontraron y dónde se resuelve cada uno.</p>
<table class="t"><tr><th>Problema encontrado (reproducido ejecutando el programa)</th><th>Solución</th><th>Capítulo</th></tr>
<tr><td><code>raffle-cli setup</code> ejecutaba primero un sorteo completo (el callback principal corre antes que los subcomandos)</td><td>comprobación de <code>ctx.invoked_subcommand</code></td><td>4</td></tr>
<tr><td>Los ganadores nunca se guardaban; <code>recreate_from_winners</code> no hacía nada</td><td>agregar cada ganador; lógica real de reanudación</td><td>6</td></tr>
<tr><td>Bucle infinito cuando hay más premios que participantes</td><td>sortear por rondas: todos ganan una vez antes de que alguien gane dos</td><td>5</td></tr>
<tr><td><code>UnboundLocalError</code> con una configuración errónea</td><td>la validación lanza errores claros y sale con código 1</td><td>6</td></tr>
<tr><td>Los CSV vacíos o solo con encabezado se aceptaban y luego fallaban</td><td>la validación reporta cada problema con número de línea</td><td>6</td></tr>
<tr><td>Se usaba <code>eval()</code> para escoger constantes; nombres con <code>[</code> dañaban la salida</td><td>sin <code>eval</code>; <code>rich.markup.escape</code></td><td>4, 8</td></tr>
<tr><td>Dependencia <code>keyboard</code> sin usar (necesita root en Linux); <code>rich</code> usado pero no declarado</td><td>se arregló <code>pyproject.toml</code></td><td>4</td></tr>
<tr><td>Un módulo de 485 líneas, sin pruebas, sin CI, sin LICENSE, README desactualizado</td><td>módulos, pruebas, CI, documentación</td><td>2, 12</td></tr>
</table>
""")
add(tip("Un hábito que vale la pena copiar", "Antes de cambiar código, escribe qué está mal y demuéstralo. La mitad de los “errores” que sospechas resultan estar bien, y la otra mitad suele ser peor de lo que pensabas."))

# 4 -------------------------------------------------------------------------
add(chapter(4, "Fundamentos de Python que aparecen en este código", "c4"))
add("<h2>4.1 Empaquetado: de una carpeta a un comando</h2>")
add("""<p>El código vive en <code>src/raffle_cli/</code>. Es el “diseño src”: como el paquete no está en el nivel superior, tus pruebas solo
pueden importarlo después de instalarlo. Eso evita un error clásico (código que funciona en tu computador solo porque estás parado en la carpeta correcta).</p>
<p><b>uv</b> es la herramienta que crea un entorno virtual (un conjunto privado de paquetes instalados para un proyecto), instala lo que pide
<code>pyproject.toml</code> y guarda las versiones exactas en <code>uv.lock</code> para que todos obtengan las mismas.
<code>uv run pytest</code> ejecuta un comando dentro de ese entorno.</p>""")
add(decision("la interfaz Textual es un extra opcional", """<p><b>Alternativa:</b> hacer de Textual una dependencia normal.
<b>Por qué no:</b> la mayoría solo quiere la interfaz clásica y Textual es una dependencia grande. Con un extra
(<code>raffle-cli[tui]</code>) se instala solo si se pide. El código lo importa de forma diferida, dentro de la rama <code>if tui:</code>,
y muestra un mensaje útil si falta. <b>Costo:</b> una cosa más que los usuarios deben recordar (<code>uvx --with textual</code>).</p>"""))

add("<h2>4.2 Anotaciones de tipo y dataclasses</h2>")
add("""<p>Una <b>dataclass</b> es una clase cuyo trabajo principal es guardar datos. Python escribe por ti <code>__init__</code>, <code>__repr__</code>
y <code>__eq__</code>. <code>frozen=True</code> hace las instancias de solo lectura, lo que además permite compararlas y usarlas como
llaves de diccionario. El texto después de los dos puntos (<code>str</code>, <code>int</code>) es una <em>anotación de tipo</em>: Python no la impone, pero tu editor y
quienes leen el código sí la aprovechan.</p>""")
add(code("raffle.py", "Participant"))
add(code("raffle.py", "Prize"))
add(code("raffle.py", "Winner"))
add(decision("dataclasses pequeñas e inmutables en vez de diccionarios", """<p>El prototipo pasaba de un lado a otro diccionarios <code>{"name": ..., "lastname": ...}</code>.
Un error de dedo como <code>row["lasname"]</code> solo falla cuando esa línea se ejecuta. Con una dataclass,
<code>p.lasname</code> lo marca tu editor de inmediato, las pruebas pueden comparar objetos completos con <code>==</code> y
<code>frozen</code> garantiza que nadie modifique un premio por accidente. <b>Alternativa:</b> modelos de Pydantic (más funciones, más peso; usamos Pydantic solo donde
vale la pena: validar <code>config.yaml</code>).</p>"""))
add("<p>La línea <code>from __future__ import annotations</code> al inicio de cada módulo vuelve las anotaciones de tipo cadenas diferidas, así que la sintaxis moderna como <code>list[str] | None</code> es segura en Python 3.10.</p>")

add("<h2>4.3 pathlib, csv y codificaciones</h2>")
add("""<p><code>pathlib.Path</code> trata las rutas como objetos: <code>base / "winners.csv"</code> une rutas correctamente en Windows y Linux.
El módulo <code>csv</code> se encarga de las comillas (un premio llamado <code>Mug, large</code> sigue siendo una sola celda). Un detalle del mundo real:
Excel guarda los CSV con una <em>marca de orden de bytes</em> invisible al inicio. Abrimos los archivos con <code>encoding="utf-8-sig"</code>, que la elimina en silencio;
de lo contrario la primera columna se llamaría <code>\\ufeffname</code> y la validación fallaría por una razón misteriosa.</p>""")

add("<h2>4.4 Excepciones que llevan información</h2>")
add(code("files.py", "DataFileError"))
add("""<p>Una excepción es solo una clase. Esta guarda <em>todos</em> los problemas encontrados en un archivo, no solo el primero. Quien arregla una
hoja de cálculo quiere ver todas las filas incorrectas de una vez. La línea de comandos la captura e imprime una lista, así los usuarios nunca ven un
traceback por sus propios errores de digitación.</p>""")

add("<h2>4.5 Pydantic para el archivo de configuración</h2>")
add(code("config.py", "RaffleConfig"))
add("""<p>Pydantic revisa la forma de los datos usando las anotaciones de tipo. Si alguien escribe <code>recreate_from_winners: maybe</code>, Pydantic
lanza <code>ValidationError</code>, que <code>load_config</code> convierte en un solo mensaje legible. Las rutas se
resuelven relativas a la carpeta del archivo de configuración (<code>resolved()</code>), así que <code>raffle-cli -c event/config.yaml</code> funciona desde cualquier lugar.</p>""")

add("<h2>4.6 Typer: convertir funciones en comandos</h2>")
add("""<p><b>Typer</b> lee los parámetros de una función y construye la línea de comandos a partir de ellos. <code>@app.command()</code> agrega un subcomando
(<code>setup</code>, <code>fireworks</code>); <code>@app.callback(invoke_without_command=True)</code> define el código que corre para
<code>raffle-cli</code> mismo y guarda las opciones globales.</p>""")
add(lines_of("cli.py", "@app.callback", "ctx.obj = {", caption="src/raffle_cli/cli.py · el callback principal (inicio)"))
add(lines_of("cli.py", "    if ctx.invoked_subcommand is not None:", "build_raffle(config or", caption="… y lo que hace después"))
add(decision("una guarda en el callback en vez de un comando “run” aparte", """<p>El callback del prototipo ejecutaba el sorteo <em>siempre</em>, incluso con
<code>raffle-cli setup</code>. La corrección son dos líneas: si Typer indica que se pidió un subcomando
(<code>ctx.invoked_subcommand</code>), se retorna de inmediato. <b>Alternativa:</b> un <code>raffle-cli run</code> dedicado; más limpio en teoría, pero rompería el
simple y fácil de recordar <code>raffle-cli</code> del README original. <b>Costo:</b> opciones como <code>--seed</code> viven en el callback, así que van
<em>antes</em> del nombre de un subcomando.</p>"""))
add("""<p><code>Annotated[bool, typer.Option("--fast", help="…")] = False</code> se lee así: “un bool, expuesto como la opción <code>--fast</code> con este texto de ayuda,
por defecto False”. Los errores pasan por una sola función, <code>fail()</code>, que imprime en rojo y devuelve <code>typer.Exit(1)</code>; el código de salida distinto de cero
permite que los scripts detecten el fallo.</p>""")

add("<h2>4.7 Rich: color sin dolor</h2>")
add("""<p><b>Rich</b> imprime texto con estilo usando un pequeño lenguaje de marcado: <code>[bold green]hola[/]</code>. El problema: los datos del usuario pueden contener corchetes.
Un participante llamado <code>[bold]Eve</code> se interpretaría como marcado. Todos los lugares que imprimen nombres usan <code>rich.markup.escape()</code>.</p>""")

# 5 -------------------------------------------------------------------------
add(chapter(5, "El motor del sorteo", "c5"))
add("""<p><code>raffle.py</code> es el corazón. No importa ninguna biblioteca de interfaz, no imprime nada y no toca archivos. Por eso es
fácil de probar y por eso <em>dos</em> interfaces distintas (clásica y Textual) pueden compartirlo sin duplicar una sola línea de la lógica del sorteo.</p>
<h2>5.1 El modelo de datos: una pila de unidades de premio</h2>""")
add(code("raffle.py", "Raffle.__init__"))
add("""<p>En vez de llevar la cuenta de “Mug: quedan 2”, el constructor expande cada premio en <em>una entrada por cada objeto físico</em>:
<code>["Mug", "Mug", "Pen", ...]</code>. Entregar un premio es simplemente <code>pop(0)</code>. Contar los premios restantes es contar la lista.
Menos casos especiales significa menos errores.</p>""")
add(code("raffle.py", "order_prizes"))
add(decision("nunca modificar los datos de quien llama", """<p>El prototipo restaba <code>prize["qty"]</code> en el mismo lugar, así que la misma lista no se podía reutilizar
(para una segunda ejecución, una prueba o volver a dibujar). <code>order_prizes</code> devuelve una lista <em>nueva</em>; <code>Prize</code> es inmutable; el motor guarda sus propias
<code>_units</code>. Una prueba (<code>test_prizes_are_not_mutated</code>) lo asegura.</p>"""))
add("<h2>5.2 Cómo se elige un ganador</h2>")
add(D.draw_flow())
add(code("raffle.py", "Raffle.draw"))
add("""<p>La idea central cabe en una línea: <code>keys = [(wins, holds_item) ...]</code>. Python compara las tuplas elemento por elemento, así que <code>(0, False)</code> va antes que
<code>(1, False)</code>, que va antes que <code>(1, True)</code>. <code>min(keys)</code> da la llave de quien “más lo merece”; <code>pool</code> son todos los que la comparten;
<code>rng.choice(pool)</code> es el único paso aleatorio. Las reglas salen de la tupla:</p>
<ul><li><b>Nadie gana dos veces antes de que todos hayan ganado una</b> (primer elemento: menos victorias).</li>
<li><b>En rondas posteriores, evitar darle a alguien un objeto que ya tiene</b> (segundo elemento), salvo que no haya alternativa.</li></ul>""")
add("<h3>Un ejemplo resuelto</h3><p>Tres personas (Ana, Ben, Cy), premios Mug×2, Pen×2, Sticker×1. El orden <code>high-low</code> (estable) da <code>units = [Mug, Mug, Pen, Pen, Sticker]</code>. Una ejecución posible:</p>")
add("""<table class="t"><tr><th>#</th><th>Premio</th><th>Grupo (llave más pequeña)</th><th>Ganador</th><th>Victorias después (Ana, Ben, Cy)</th></tr>
<tr><td>1</td><td>Mug</td><td>Ana, Ben, Cy: todos (0, no)</td><td>Ben</td><td>0, 1, 0</td></tr>
<tr><td>2</td><td>Mug</td><td>Ana, Cy: aún con 0 victorias</td><td>Cy</td><td>0, 1, 1</td></tr>
<tr><td>3</td><td>Pen</td><td>Ana: la única con 0 victorias</td><td>Ana</td><td>1, 1, 1</td></tr>
<tr><td>4</td><td>Pen</td><td>Ben, Cy: Ana es (1, <b>tiene Pen</b>), así que va detrás de ellos</td><td>Cy</td><td>1, 1, 2</td></tr>
<tr><td>5</td><td>Sticker</td><td>Ana, Ben: menos victorias (1)</td><td>Ben</td><td>1, 2, 2</td></tr></table>
<p>Cinco premios, tres personas: nadie recibió un segundo premio hasta el sorteo 4, porque solo entonces todos habían ganado una vez. Esa es exactamente la regla “si hay más premios que participantes, la gente recibe más de uno”.</p>""")
add(decision("rondas en vez de “elegir a cualquiera y luego cambiar”", """<p>El prototipo escogía una persona al azar con reemplazo; si ya tenía un premio preguntaba “¿cambiar?”. Eso
volvía el sorteo interactivo de una forma confusa, y se quedaba en un bucle infinito cuando había más premios que personas, porque cambiar nunca reducía la pila.
<b>Nuestra regla:</b> sortear entre quienes tienen menos victorias. Es fácil de explicar a una audiencia, nunca entra en bucle infinito y es demostrablemente justa (las pruebas verifican que con
10 premios y 5 personas cada una recibe exactamente dos). <b>Costo:</b> eliminamos la pregunta de cambio. Podría volver como opción.</p>"""))
add(decision("los participantes se identifican por posición, no por nombre", """<p>Dos personas pueden tener el mismo nombre. Si los ganadores se buscaran por <code>(name, lastname)</code>, se fundirían en uno.
El motor guarda <code>_wins</code> y <code>_held</code> como listas indexadas por la posición del participante, así que los duplicados son dos oportunidades distintas.
El lector de CSV solo imprime una <em>advertencia</em> por duplicados.</p>"""))
add("<h2>5.3 Reconstruir el estado: reanudar</h2>")
add(code("raffle.py", "Raffle._restore"))
add("""<p>Al reanudar, cada ganador guardado se reproduce: se quita ese premio de la pila y se cuenta la victoria. Si el archivo guardado contradice el archivo de premios
(un objeto que ya no existe, una persona que ya no está) lanzamos un <code>ValueError</code> claro en vez de adivinar.</p>""")

# 6 -------------------------------------------------------------------------
add(chapter(6, "Archivos, validación y reanudación", "c6"))
add("<h2>6.1 Leer un CSV a la defensiva</h2>")
add("""<p>La regla para todo lo que escribe un humano: <b>asume que está mal y explica exactamente cómo</b>. Los tres lectores comparten una función auxiliar que revisa el encabezado
y devuelve las filas con sus números de línea.</p>""")
add(code("files.py", "_read_rows"))
add(code("files.py", "read_prizes"))
add(decision("reunir todos los problemas y nunca “reparar” los archivos del usuario", """<p>Dos decisiones aquí.</p>
<p><b>1. Reportar todos los problemas a la vez.</b> Fallar en la primera fila mala significa diez ciclos de editar y ejecutar para diez errores. El lector junta una lista y lanza el error una sola vez.</p>
<p><b>2. Sin arreglos automáticos.</b> El prototipo ofrecía “¿quieres poner el contenido por defecto?”, lo que sobrescribiría una lista real de participantes si presionabas
<code>y</code> por reflejo. Ahora un archivo dañado produce un mensaje de error y se deja intacto; <code>setup</code> solo escribe archivos que no existen (o cuando pasas <code>--force</code>).</p>
<p>Detalles menores: los encabezados se pasan a minúsculas y se recortan, las celdas se recortan, las líneas en blanco se ignoran y <code>qty</code> debe ser un entero ≥ 1.</p>"""))
add("<h2>6.2 Guardar cada ganador de inmediato</h2>")
add(code("files.py", "append_winner"))
add("""<p>Si el portátil se apaga en medio de un meetup, no deberías perder los ganadores ya anunciados. Por eso un ganador se agrega a <code>winners.csv</code> en el momento en que se revela,
no al final. Agregar una sola fila además es barato y seguro.</p>""")
add("<h2>6.3 Empezar de cero o reanudar</h2>")
add(D.resume_flow())
add(decision("el ganador se decide primero y se guarda al revelarlo", """<p><code>raffle.draw()</code> escoge al ganador <em>antes</em> del suspenso, luego la interfaz reproduce la animación, y solo cuando se revela el nombre llamamos al
callback <code>on_winner</code> que escribe el CSV. <b>Por qué:</b> la interfaz puede mostrar lo que quiera mientras el resultado ya está fijo (los rodillos de la tragamonedas simplemente aterrizan en él), y el archivo nunca contiene un ganador que la audiencia no haya visto aún.
<b>Costo:</b> si sales durante un giro, ese premio no queda registrado y se sorteará de nuevo al reanudar (posiblemente otra persona): es el comportamiento correcto para un evento en vivo.</p>"""))
add(decision("los resultados anteriores se respaldan, no se borran", """<p>Con <code>recreate_from_winners: false</code> el programa empieza vacío, pero antes copia un <code>winners.csv</code> no vacío a
<code>winners.csv.bak</code> (ver <code>reset_winners</code>). Borrar resultados en silencio es el tipo de error que solo cometes una vez, frente a una audiencia.</p>"""))

# 7 -------------------------------------------------------------------------
add(chapter(7, "Aleatoriedad, justicia y --seed", "c7"))
add("""<p>Los computadores no producen números verdaderamente aleatorios; <code>random.Random(seed)</code> es un <em>generador pseudoaleatorio</em>: dale la misma
semilla y produce la misma secuencia siempre. Suena como un defecto, pero para un sorteo transparente es una ventaja.</p>
<ul><li>Si no se da una semilla, se genera una con <code>secrets.randbits(32)</code> y se <b>muestra en los resultados</b>.</li>
<li>Cualquiera con los mismos archivos y la misma <code>--seed</code> puede reproducir exactamente los mismos ganadores.</li></ul>""")
add(decision("mostrar la semilla en vez de ocultar el azar", """<p><b>Alternativa:</b> <code>random.SystemRandom()</code>, que toma la entropía del sistema operativo: impredecible, pero nadie puede verificar jamás un resultado.
Para regalar stickers, la <em>auditabilidad</em> pesa más que el secreto. Una semilla de 32 bits no es criptográficamente fuerte y eso está bien: es un recibo, no un secreto.
(Si los premios tuvieran valor en dinero, querrías comprometerte públicamente con la semilla antes del sorteo.)</p>"""))
add("<h2>7.1 Un error que encontramos pensando</h2>")
add("""<p>La primera versión de Textual hacía el efecto de “nombres que pasan borrosos” llamando a <code>raffle.rng.choice(...)</code>. Cada llamada consume un número del
generador, así que la animación del giro cambiaba <em>quién ganaba el siguiente premio</em>: la misma semilla daba ganadores distintos en la interfaz clásica y en la de
Textual, y con <code>--fast</code> (menos pasos de animación) frente a velocidad normal. La solución: la tragamonedas tiene su propio generador aparte.</p>""")
add(D.two_rngs())
add(tip("Regla práctica", "Todo lo que deba ser reproducible tiene su propio generador aleatorio, y nada cosmético puede tocarlo. Una prueba (<code>test_tui_animation_leaves_the_seeded_draw_untouched</code>) ahora lo vigila."))

# 8 -------------------------------------------------------------------------
add(chapter(8, "La interfaz clásica de terminal", "c8"))
add("""<p><code>ui.py</code> es la primera “cara”. Recibe un <code>Raffle</code> listo y una función <code>on_winner</code> y se ocupa solo de la presentación.</p>""")
add(code("ui.py", "run"))
add("""<p>Fíjate en lo que <em>no</em> sabe: cómo se eligen los ganadores (<code>raffle.draw()</code>) ni dónde se guardan (<code>on_winner</code>). Pasar una función como argumento
así se llama <b>callback</b>; mantiene la interfaz y el almacenamiento independientes.</p>
<ul><li><code>delayed()</code> imprime palabra por palabra con <code>time.sleep</code> para crear suspenso; <code>--fast</code> pone la pausa en cero.</li>
<li><code>pause()</code> espera Enter, pero captura <code>EOFError</code> para que el programa no falle cuando la entrada viene por una tubería (por ejemplo <code>echo | raffle-cli</code> en un script).</li>
<li>El mismo objeto <code>Raffle</code> se muestra en tablas mediante <code>raffle.remaining</code> y <code>raffle.winners</code>.</li></ul>""")
add(code("ui.py", "pause"))

# 9 -------------------------------------------------------------------------
add(chapter(9, "Los fuegos artificiales", "c9"))
add("""<p>Los fuegos artificiales son una primera <em>simulación</em> clásica: mantén una lista de cosas en movimiento, actualiza cada una un poquito por “tic”, dibújalas todas y repite 20 veces por segundo.
Hay dos tipos de cosas: <b>cohetes</b> (suben y luego explotan) y <b>chispas</b> (salen disparadas, frenan, caen y se apagan).</p>""")
add(D.fireworks_life())
add(code("fireworks.py", "Fireworks.step"))
add(code("fireworks.py", "Fireworks._explode"))
add("""<p>Tres pedacitos de matemáticas hacen el trabajo:</p>
<ul><li><b>Ángulo:</b> <code>2π · i / count</code> reparte las chispas de forma pareja alrededor de un círculo. Las explosiones “ring” usan todas la misma velocidad; las “burst” usan velocidades al azar.</li>
<li><b>Proporción de aspecto:</b> las celdas de la terminal son aproximadamente el doble de altas que de anchas, así que la velocidad horizontal se multiplica por <code>ASPECT = 2</code>. Sin eso, los círculos se ven como óvalos altos.</li>
<li><b>Fricción y gravedad:</b> en cada tic la velocidad se multiplica por 0,9 (resistencia del aire) y la gravedad suma 0,035 a la velocidad hacia abajo. Una chispa con velocidad 0,75 recorre unas
<code>0,75 / (1 − 0,9) ≈ 7,5</code> filas antes de detenerse, que es justo lo adecuado para una terminal.</li></ul>""")
add("<h2>9.1 Dibujar un cuadro</h2>")
add("""<p><code>render()</code> crea una cuadrícula vacía de caracteres, “dibuja” en ella cada cohete y cada chispa (el carácter depende de cuánta vida le queda: <code>*</code>, <code>+</code>, <code>.</code>),
superpone el título y el texto del ganador, y devuelve un solo <code>rich.text.Text</code>. Nota que <code>Fireworks</code> nunca imprime nada por sí mismo.</p>""")
add(code("fireworks.py", "play"))
add(decision("una simulación, dos formas de dibujarla", """<p><code>Fireworks</code> solo produce un <code>Text</code>. <code>play()</code> lo muestra con <code>Live(screen=True)</code> de Rich (la “pantalla alterna” de la terminal, que se restaura
después, como <code>vim</code> o <code>less</code>), y la interfaz Textual muestra el mismo objeto dentro de un widget <code>Static</code> refrescado por un temporizador.
<b>Alternativas:</b> un programa con curses (no portable a Windows) o una biblioteca de fuegos artificiales (una dependencia para 200 líneas de código). <b>Costo:</b> implementamos la física nosotros mismos, lo que además
es más divertido para aprender. No hace nada cuando no hay una terminal conectada (<code>console.is_terminal</code>), así que los scripts y las pruebas no se cuelgan.</p>"""))

# 10 ------------------------------------------------------------------------
add(chapter(10, "La interfaz Textual", "c10"))
add("""<p><b>Textual</b> es un framework para aplicaciones de terminal a pantalla completa con ideas tomadas de las páginas web: <em>widgets</em> (tablas, etiquetas, los tuyos), diseño descrito con <em>CSS</em>,
<em>eventos</em> (teclado, mouse, cambio de tamaño), <em>temporizadores</em> y <em>mensajes</em> que los widgets se envían entre sí.</p>
<h2>10.1 Un diseño que se adapta a la ventana</h2>""")
add(D.layouts())
add(lines_of("tui.py", "WIDE_AT", "BINDINGS = [", caption="src/raffle_cli/tui.py · constantes y CSS"))
add(code("tui.py", "RaffleApp._layout"))
add("""<p>La tragamonedas está en un contenedor (<code>#machine-box</code>) que por defecto es una fila de ancho completo en la parte superior. Cuando la ventana tiene al menos 120 columnas de ancho, Python agrega la clase CSS
<code>wide</code> a <code>#main</code>, y la regla <code>#main.wide #machine-box { dock: right; ... }</code> la mueve al borde derecho. Python decide <em>cuándo</em>; el CSS decide <em>cómo se ve</em>.
El cambio de tamaño lo maneja <code>on_resize</code>, que vuelve a llamar a <code>_layout</code>.</p>""")
add("<h2>10.2 Atajos de teclado y un error sorprendente</h2>")
add(code("tui.py", "RaffleApp.action_draw"))
add("""<p><code>BINDINGS</code> asocia teclas con <em>acciones</em> (métodos llamados <code>action_...</code>). Nuestra primera versión no hacía nada al presionar Enter, porque el
<code>DataTable</code> enfocado maneja Enter por su cuenta (“seleccionar esta fila”) antes de que la aplicación lo vea. La solución es <code>priority=True</code> en el atajo, que deja ganar a la aplicación.
La batería de pruebas lo detectó: presiona Enter y verifica que se sorteó un premio.</p>""")
add(decision("la aplicación le dice a los widgets qué hacer; los widgets envían mensajes de vuelta", """<p>Fíjate en que <code>action_draw</code> llama a <code>machine.pull(winner, reveal)</code> (la aplicación le ordena al widget), mientras que el widget le dice a la aplicación “me hicieron clic” <em>publicando un mensaje</em>
(<code>Pulled</code>). La aplicación nunca se mete en las entrañas del widget y el widget no sabe nada de sorteos aparte de un ganador en el que aterrizar. Es la misma idea de callback del capítulo 8.</p>"""))

# 11 ------------------------------------------------------------------------
add(chapter(11, "La máquina tragamonedas", "c11"))
add("""<p>La tragamonedas es un <b>widget propio</b>: una clase que hereda del <code>Widget</code> de Textual e implementa <code>render()</code>, devolviendo lo que se debe dibujar. Todo lo que ves es texto:
caracteres de dibujo de cajas, unos cuantos colores, y la palanca hecha de <code>●</code>, <code>┃</code> y <code>┻</code>.</p>""")
add(D.machine_anatomy())
add("""<p>Un <b>rodillo</b> es solo una lista de nombres (la tira) y un número (<code>pos</code>) que dice cuál está en la fila del medio. “Girar” significa aumentar <code>pos</code> y volver a dibujar. Para que el rodillo aterrice en el ganador,
la tira se construye <em>al revés</em>: nombres al azar, con el ganador colocado en el índice <code>steps</code>, y el rodillo se detiene cuando <code>pos</code> lo alcanza. Los nombres justo encima y debajo del ganador
se vuelven a sortear para que nunca veas el nombre del ganador dos veces.</p>""")
add(code("slot.py", "SlotMachine._start_reels"))
add("<h2>11.1 Animación sin bucle: temporizadores</h2>")
add("""<p>Podrías esperar un bucle <code>while</code> con <code>sleep</code> adentro. Eso congelaría toda la aplicación, porque Textual necesita seguir atendiendo teclas, el mouse y el dibujo. En cambio,
cada paso hace un poco de trabajo y luego le pide a Textual: “llámame de nuevo en N segundos” con <code>set_timer</code>. Entre llamadas, Textual queda libre para hacer otras cosas.</p>""")
add(code("slot.py", "SlotMachine._advance"))
add("""<p>La pausa crece con el cubo del progreso: <code>0.04 + 0.28 · (pos/steps)³</code>. Al principio las filas pasan cada 40 ms; cerca del final los intervalos se estiran a unos 0,3 s, igual que una
máquina real que va frenando. Un cubo la mantiene rápida por mucho tiempo y luego frena fuerte. El rodillo derecho tiene 12 filas más que recorrer, así que aterriza después: el clásico suspenso de “se detiene el izquierdo, luego el derecho”.</p>""")
add(D.delay_curve([18, 30]))
add(D.timeline(T1, T2, REVEAL))
add(f"""<p>El tiempo total desde que se jala la palanca hasta la revelación es de unos <b>{REVEAL:.1f} segundos</b> (calculado con la misma fórmula que usa el código). Con <code>--fast</code> las pausas bajan a 20 ms y los rodillos tienen 3 y 5 filas,
lo que hace rápidas las pruebas automáticas.</p>""")
add("<h2>11.2 La palanca y el mouse</h2>")
add(code("slot.py", "SlotMachine.pull"))
add("""<p>La palanca tiene tres estados (arriba, a medias, jalada), cada uno simplemente una fila distinta para la bola roja. <code>pull()</code> los programa uno tras otro y luego pone a girar los rodillos cuando la palanca llega abajo.
El clic funciona porque Textual llama al método <code>on_click</code> del widget con los clics del mouse; publicamos un mensaje <code>Pulled</code> y la aplicación (<code>on_slot_machine_pulled</code>) sortea.
<b>Teclado y mouse ejecutan exactamente el mismo camino de código</b>, así que no hay nada extra que probar ni mantener.</p>""")
add(D.message_flow())
add(decision("dibujar la máquina como un solo widget de texto en vez de muchos widgets pequeños", """<p><b>Alternativa:</b> armar la máquina con contenedores y etiquetas de Textual (una etiqueta por fila, un contenedor por rodillo). Sería más fácil de
estilizar por separado, pero más difícil de animar sincronizadamente y de mantener la palanca alineada. Devolver un solo <code>Text</code> desde <code>render()</code> mantiene cada cuadro consistente y toda la máquina cabe en unas ~150 líneas.
<b>Costo:</b> el arte con caracteres exige cuidado con los anchos: por eso cada línea se rellena a la misma longitud y el ancho de celda se limita a 8–12 caracteres (los nombres largos se cortan con “…”).</p>"""))

# 12 ------------------------------------------------------------------------
add(chapter(12, "Pruebas (tests)", "c12"))
add(f"""<p>Hay <b>{TOTAL} pruebas automáticas</b>: {counts.get('test_raffle', 0)} para el motor, {counts.get('test_files_config', 0)} para archivos y configuración, {counts.get('test_cli', 0)} para comandos, fuegos artificiales y la aplicación Textual.
Ejecútalas con <code>uv run pytest</code>. Una prueba es una función que prepara una situación, ejecuta el código y usa <code>assert</code> para afirmar lo que debe ser verdad. Si alguna afirmación es falsa, la prueba falla y te dice cuál.</p>""")
add(D.test_layers())
add("""<p>La pirámide explica la estructura: muchas pruebas rápidas en la base para la lógica pura (milisegundos, sin archivos, sin pantalla), menos pruebas de más alto nivel arriba que ejercitan todo junto.
Como separamos el motor de las interfaces en el capítulo 2, las reglas más importantes se pueden probar sin ninguna pantalla.</p>""")
add(lines_of("tests/test_raffle.py", "def test_more_prizes_than_participants", "== {2}", caption="tests/test_raffle.py · tu regla “más premios que personas”"))
add(lines_of("tests/test_raffle.py", "def test_same_seed_same_result", "assert a == b", caption="tests/test_raffle.py · reproducibilidad"))
add(code("tests/test_cli.py", "test_tui_lever_click_draws_and_layout_is_responsive", "tests/test_cli.py · manejando la aplicación Textual real sin pantalla"))
add(decision("pytest + el Pilot de Textual, sin pytest-asyncio", """<p>Textual ofrece <code>app.run_test()</code>, que ejecuta la aplicación sin una terminal real y te da un <b>Pilot</b>
para presionar teclas, hacer clic en widgets y cambiar el tamaño de la “terminal”. El cuerpo de la prueba es <code>async</code>, así que lo envolvemos con <code>asyncio.run(go())</code> dentro de una función de prueba normal. <b>Alternativa:</b> el
plugin <code>pytest-asyncio</code>, una dependencia más que explicar. <b>Costo:</b> unas cuantas llamadas a <code>pause()</code> para esperar los temporizadores; <code>--fast</code> las mantiene cortas.</p>"""))
add(tip("Lo que las pruebas no pueden decirte", "Todas estas pruebas pasan sin que nadie mire la pantalla. Las fuentes, cómo se ve la palanca en tu terminal y si los fuegos artificiales <em>se sienten</em> bien siguen necesitando tus propios ojos. Ejecuta el programa de verdad antes de un evento."))

# 13 ------------------------------------------------------------------------
add(chapter(13, "Decisiones técnicas en una tabla", "c13"))
add("""<p>Las mismas decisiones explicadas en los capítulos, como referencia rápida. <em>Costo</em> es a lo que renuncias.</p>
<table class="t dec"><tr><th>Decisión</th><th>Alternativa</th><th>Por qué</th><th>Costo</th></tr>
<tr><td>Motor en un módulo puro (<code>raffle.py</code>)</td><td>lógica dentro del código de la interfaz</td><td>se puede probar y lo comparten ambas interfaces</td><td>un archivo más que aprender</td></tr>
<tr><td>Dataclasses inmutables</td><td>dicts / Pydantic</td><td>a prueba de errores de dedo, comparables, inmutables</td><td>sin conversión automática</td></tr>
<tr><td>Premios como lista de unidades</td><td>contadores por premio</td><td>menos casos especiales</td><td>la lista crece con el total de premios (diminuto)</td></tr>
<tr><td>Sorteo por la mínima <code>(wins, holds_item)</code></td><td>azar con pregunta de cambio</td><td>justo, explicable, nunca entra en bucle</td><td>se eliminó el cambio de premio</td></tr>
<tr><td>Personas identificadas por posición</td><td>por nombre</td><td>se permiten nombres duplicados</td><td>necesita una advertencia de duplicados</td></tr>
<tr><td>Semilla visible, <code>Random(seed)</code></td><td><code>SystemRandom</code></td><td>auditable, reproducible</td><td>no es secreta (bien para regalos)</td></tr>
<tr><td>Generador aleatorio cosmético aparte</td><td>reutilizar el del sorteo</td><td>la animación no puede cambiar a los ganadores</td><td>dos generadores que recordar</td></tr>
<tr><td>Decidir primero, guardar al revelar</td><td>guardar al sortear</td><td>el archivo no adelanta la revelación</td><td>salir a medio giro vuelve a sortear</td></tr>
<tr><td>Agregar ganadores uno a uno</td><td>escribir todo al final</td><td>a prueba de caídas</td><td>muchas escrituras pequeñas (diminuto)</td></tr>
<tr><td>Validar listando todos los problemas</td><td>fallar en el primer error</td><td>arreglar todo de una vez</td><td>un poco más de código</td></tr>
<tr><td>Nunca reparar automáticamente los archivos del usuario</td><td>ofrecer valores por defecto ante un error</td><td>no puede sobrescribir datos reales</td><td>el usuario arregla a mano</td></tr>
<tr><td>Rutas relativas al archivo de configuración</td><td>relativas a la carpeta del terminal</td><td>funciona desde cualquier lugar</td><td>algo sorprendente para algunos</td></tr>
<tr><td>Pydantic solo para la configuración</td><td>revisiones manuales de dict</td><td>errores claros con poco código</td><td>una dependencia</td></tr>
<tr><td>Callback de Typer con <code>invoke_without_command</code></td><td>subcomando <code>run</code> explícito</td><td>mantiene el simple <code>raffle-cli</code></td><td>las opciones van antes del subcomando</td></tr>
<tr><td>Textual como extra opcional, importación diferida</td><td>siempre instalado</td><td>instalación liviana por defecto</td><td>un paso extra de instalación</td></tr>
<tr><td>Simulación de fuegos artificiales propia</td><td>curses / biblioteca</td><td>portable, diminuta, educativa</td><td>mantenemos la física nosotros</td></tr>
<tr><td>Una simulación, dos formas de dibujarla</td><td>dos implementaciones</td><td>sin lógica duplicada</td><td>el dibujo solo devuelve <code>Text</code></td></tr>
<tr><td><code>Live(screen=True)</code> de Rich</td><td>imprimir cuadros y limpiar</td><td>sin parpadeo, la terminal se restaura</td><td>necesita una terminal real</td></tr>
<tr><td>Atajo con prioridad para Enter</td><td>hacer las tablas no enfocables</td><td>una línea, la tecla siempre funciona</td><td>tapa el Enter del widget</td></tr>
<tr><td>Una clase CSS cambia el diseño a las 120 columnas</td><td>dos pantallas separadas</td><td>un solo diseño, poco código</td><td>punto de corte fijo</td></tr>
<tr><td>Tragamonedas = un solo widget propio</td><td>muchos widgets pequeños</td><td>los cuadros se mantienen consistentes</td><td>cuidado con los anchos del texto</td></tr>
<tr><td>Nombres en texto plano, sin fuente ASCII-art</td><td>letras grandes con figlet</td><td>nombres largos y tildes rompen el arte</td><td>nombres más pequeños</td></tr>
<tr><td>Temporizadores en vez de bucles con <code>sleep</code></td><td>animación bloqueante</td><td>la interfaz sigue respondiendo</td><td>callbacks más difíciles de leer</td></tr>
<tr><td><code>asyncio.run</code> en las pruebas</td><td>pytest-asyncio</td><td>sin plugin extra</td><td>un poco de código repetitivo</td></tr>
<tr><td>Python ≥ 3.10, uv + archivo de bloqueo</td><td>solo versiones nuevas / pip freeze</td><td>amplio soporte, instalaciones reproducibles</td><td>la sintaxis antigua limita</td></tr>
</table>""")

# 14 ------------------------------------------------------------------------
add(chapter(14, "Lo que salió mal (y lo que enseñó)", "c14"))
add("""<p>Los proyectos reales no avanzan en línea recta. Estos son los desvíos reales, porque las historias de depuración enseñan más que el código pulido.</p>
<table class="t"><tr><th>Qué pasó</th><th>Causa</th><th>Lección</th></tr>
<tr><td>Presionar Enter en la aplicación Textual no hacía nada</td><td>La tabla enfocada manejó Enter primero</td><td>Los eventos van primero al widget enfocado; usa <code>priority=True</code>. Las pruebas que simulan teclas lo encuentran en segundos.</td></tr>
<tr><td>El mensaje “instala el extra tui” se cortó a <code>pip install 'raffle-cli'</code></td><td>Rich leyó <code>[tui]</code> como marcado y se lo tragó</td><td>Escapa todo lo visible para el usuario que pueda contener corchetes (<code>rich.markup.escape</code>).</td></tr>
<tr><td><code>uvx ... --tui</code> falló en una máquina nueva</td><td><code>uvx</code> no instala extras opcionales si no se piden</td><td>Documenta el comando exacto (<code>--with textual</code>) y haz que el error lo diga.</td></tr>
<tr><td>Misma semilla, ganadores distintos en las dos interfaces</td><td>La animación consumía números del generador del sorteo</td><td>Separa la aleatoriedad que debe ser reproducible de la que es decoración.</td></tr>
<tr><td>Los nombres grandes en ASCII-art se veían impresionantes y luego se descartaron</td><td>Nombres largos, tildes y letras no latinas se desbordan o se dibujan en blanco</td><td>Las funciones que necesitan manejar anchos para cualquier entrada posible son caras. El texto plano más simple gana en una terminal.</td></tr>
<tr><td>La primera idea del giro mostraba un nombre a la vez</td><td>Queríamos “un giro literal”</td><td>Pasar a rodillos (una lista y un puntero) hizo el efecto más convincente <em>y</em> más simple que el código anterior.</td></tr>
</table>""")

# 15 ------------------------------------------------------------------------
add(chapter(15, "Ejercicios", "c15"))
add("""<p>Aquí es donde recuperas el código. Están ordenados del más fácil al más difícil. Para cada uno, escribe primero una prueba (o al menos ejecuta el programa y mira).</p>
<table class="t"><tr><th>#</th><th>Ejercicio</th><th>Dónde mirar</th><th>Pista</th></tr>
<tr><td>1</td><td>Cambia los colores de los fuegos artificiales y haz que duren más</td><td><code>fireworks.py</code> <code>PALETTE</code>, segundos en <code>ui.py</code></td><td>Ejecuta <code>raffle-cli fireworks --seconds 20</code> mientras ajustas.</td></tr>
<tr><td>2</td><td>Agrega un nuevo valor de <code>--order</code>, <code>alpha</code> (premios de la A a la Z)</td><td><code>raffle.py</code> <code>ORDERS</code>, <code>order_prizes</code></td><td>Un <code>elif</code> y una prueba. <code>sort(key=lambda p: p.item.lower())</code>.</td></tr>
<tr><td>3</td><td>Imprime una frase al final: “N ganadores, M premios”</td><td><code>ui.show_results</code></td><td>Tienes <code>raffle.winners</code> y <code>raffle.remaining</code>.</td></tr>
<tr><td>4</td><td>Agrega una columna opcional <code>email</code> a los participantes que el sorteo ignore</td><td><code>files.py</code>, <code>raffle.py</code></td><td>La revisión del encabezado es estricta: decide cómo permitir columnas extra y prueba ambos casos.</td></tr>
<tr><td>5</td><td>Agrega una opción <code>--exclude "Nombre Apellido"</code> para personas presentes pero no elegibles (organizadores)</td><td><code>cli.py</code> <code>build_raffle</code></td><td>Filtra la lista de participantes antes de crear el <code>Raffle</code>.</td></tr>
<tr><td>6</td><td>Exporta un archivo de resultados en Markdown junto a <code>winners.csv</code></td><td>nueva función en <code>files.py</code></td><td>Llámala después del último premio en <code>main</code>.</td></tr>
<tr><td>7</td><td>Agrega un tercer rodillo que muestre el premio en la tragamonedas</td><td><code>slot.py</code></td><td>La lista de rodillos está hecha para 2; generalízala. Ojo con el ancho total y el ancho del dock en el CSS (52).</td></tr>
<tr><td>8</td><td>Agrega una columna <code>weight</code> para que algunas personas tengan más oportunidades</td><td><code>raffle.py</code> <code>draw</code></td><td>Piensa primero en la justicia: ¿cómo interactúa con “todos ganan una vez antes de que alguien gane dos”? Escribe esa regla antes de programar.</td></tr>
</table>""")

# 16 ------------------------------------------------------------------------
add(chapter(16, "Glosario y cómo ejecutar todo", "c16"))
add("""<h2>Ejecútalo</h2>
<p><b>Sin instalar (macOS / Linux):</b></p>""")
add(snip("""R="git+https://github.com/andoresuperesu/raffle-cli"
uvx --from $R raffle-cli setup
uvx --from $R --with textual raffle-cli --tui""", "bash", "bash / zsh"))
add("<p><b>PowerShell:</b></p>")
add(snip("""$R = "git+https://github.com/andoresuperesu/raffle-cli"
uvx --from $R raffle-cli setup
uvx --from $R --with textual raffle-cli --tui""", "powershell", "PowerShell"))
add("<p><b>Desde un clon, para desarrollar:</b></p>")
add(snip("""git clone https://github.com/andoresuperesu/raffle-cli
cd raffle-cli
uv sync
uv run pytest
uv run raffle-cli --config examples/config.yaml --tui""", "bash", "cualquier shell"))
add("""<h2>Límites conocidos</h2>
<ul><li>Desarrollado y probado en Linux. En Windows usa Windows Terminal; los caracteres de dibujo de cajas y la entrada del mouse no están verificados allí.</li>
<li>Las pruebas demuestran el comportamiento, no la apariencia: revisa visualmente la tragamonedas y los fuegos artificiales antes de un evento.</li>
<li>La semilla de 32 bits hace los sorteos reproducibles, no secretos (ver capítulo 7).</li></ul>
<h2>Glosario</h2>
<table class="t gloss">
<tr><td><b>Callback</b></td><td>Una función que le entregas a otro código para que te llame de vuelta más tarde (<code>on_winner</code>, <code>reveal</code>).</td></tr>
<tr><td><b>CLI</b></td><td>Interfaz de línea de comandos: un programa que controlas escribiendo un comando.</td></tr>
<tr><td><b>Dataclass</b></td><td>Una clase pensada para guardar datos; Python genera los métodos aburridos.</td></tr>
<tr><td><b>Punto de entrada (entry point)</b></td><td>La función que llama un comando como <code>raffle-cli</code>; se declara en <code>pyproject.toml</code>.</td></tr>
<tr><td><b>Extra</b></td><td>Dependencias opcionales que se instalan con <code>paquete[nombre]</code>.</td></tr>
<tr><td><b>Frozen (inmutable)</b></td><td>Un objeto que no se puede modificar después de creado.</td></tr>
<tr><td><b>Pilot</b></td><td>El conductor de pruebas de Textual que presiona teclas y hace clics en una aplicación sin pantalla.</td></tr>
<tr><td><b>Pseudoaleatorio</b></td><td>Parece aleatorio pero se calcula a partir de una semilla, así que se puede repetir.</td></tr>
<tr><td><b>Función / módulo puro</b></td><td>Solo calcula a partir de sus entradas: sin imprimir, sin archivos, sin reloj.</td></tr>
<tr><td><b>Semilla (seed)</b></td><td>El número inicial de un generador pseudoaleatorio.</td></tr>
<tr><td><b>Separación de responsabilidades</b></td><td>Dividir un programa para que cada parte tenga un solo trabajo.</td></tr>
<tr><td><b>Tic (tick)</b></td><td>Un paso de una simulación o animación.</td></tr>
<tr><td><b>TUI</b></td><td>Interfaz de usuario de texto: una aplicación a pantalla completa dibujada con caracteres.</td></tr>
<tr><td><b>Entorno virtual</b></td><td>Una carpeta privada de paquetes instalados para un proyecto (<code>.venv</code>).</td></tr>
<tr><td><b>Widget</b></td><td>Una pieza reutilizable de una interfaz de usuario (una tabla, una etiqueta, la tragamonedas).</td></tr>
</table>
<h2>Dónde seguir leyendo</h2>
<ul><li>Typer: typer.tiangolo.com &nbsp;·&nbsp; Rich: rich.readthedocs.io &nbsp;·&nbsp; Textual: textual.textualize.io</li>
<li>Pydantic: docs.pydantic.dev &nbsp;·&nbsp; pytest: docs.pytest.org &nbsp;·&nbsp; uv: docs.astral.sh/uv</li>
<li>El tutorial de Python sobre clases, excepciones y módulos: docs.python.org/es/3/tutorial</li></ul>
""")
