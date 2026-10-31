# **El Patrón de Diseño Command: Fundamentos Teóricos, Arquitectura e Implementación Avanzada**

## **Introducción y Concepto Teórico del Patrón Command**

El patrón de diseño Command, categorizado dentro de los patrones de comportamiento por la Gang of Four (GoF), constituye una abstracción fundamental para la reificación de invocaciones de métodos en sistemas orientados a objetos. Su principio rector reside en transformar una petición, operación o acción en un objeto autónomo de primera clase que encapsula toda la información requerida para ejecutar dicha acción en un instante posterior. Al formalizar esta encapsulación, se elimina la dependencia directa entre el componente que solicita la ejecución —conocido como emisor o *invoker*— y el componente que posee la lógica de negocio concreta para procesarla, denominado receptor o *receiver*.

Esta separación de responsabilidades responde de forma rigurosa a los principios del diseño orientado a objetos en la arquitectura de software moderna. Por un lado, el Principio de Responsabilidad Única (SRP) se satisface al aislar el mecanismo que desencadena la acción de la implementación operativa real. Por otro lado, el Principio de Abierto/Cerrado (OCP) se cumple plenamente, ya que es posible incorporar nuevas operaciones o tipos de comandos al sistema sin necesidad de modificar el código fuente de los invocadores o de la interfaz de usuario existente. La trascendencia de este enfoque radica en que, al convertir una llamada a un método en una entidad manipulable, la ejecución deja de ser un evento efímero en el tiempo y se convierte en un dato persistente capaz de ser almacenado, transmitido a través de una red, encolado en un proceso en segundo plano, auditado o revertido dentro del ciclo de vida de la aplicación.

## **Componentes Estructurales y Roles en la Arquitectura**

La topología del patrón Command se articula mediante cinco roles con responsabilidades claramente delimitadas, cuya interacción armónica permite minimizar el acoplamiento entre los módulos del sistema. En el núcleo de esta estructura se encuentra la interfaz o clase abstracta Command, la cual declara una firma de método uniforme —comúnmente denominada `execute()`— y, cuando el dominio lo requiere, métodos adicionales como `undo()` para revertir los efectos de la operación. Esta abstracción actúa como el contrato universal a través del cual los invocadores interactúan con cualquier acción sin conocer los pormenores de su procesamiento.

Las clases de tipo ConcreteCommand implementan dicho contrato y funcionan como el puente de enlace entre la abstracción y la infraestructura operativa. Cada comando concreto almacena el contexto de la petición, incluyendo los parámetros de entrada y una referencia directa al receptor responsable de ejecutar la tarea. Al momento de invocarse el método de ejecución, el comando concreto no realiza el procesamiento denso de la lógica por sí mismo, sino que delega la llamada hacia las rutinas pertinentes de la clase Receiver. El receptor puede ser cualquier clase del dominio con la capacidad técnica de cumplir con la solicitud. Por su parte, el emisor o Invoker sostiene la referencia hacia el objeto comando y dispara su ejecución como respuesta a eventos del sistema, tales como la interacción con un elemento de la interfaz gráfica o el vencimiento de un temporizador. Finalmente, el rol del Client ensambla la arquitectura instanciando los receptores, creando los comandos concretos parametrizados y vinculándolos formalmente a los invocadores correspondientes.

| Componente | Rol en el Sistema | Nivel de Acoplamiento | Responsabilidad Principal |
| :--- | :--- | :--- | :--- |
| **Command** | Interfaz de Abstracción | Nulo (Contrato abstracto) | Declara la firma del método de ejecución y de reversión para todas las operaciones. |
| **ConcreteCommand** | Enlace y Encapsulamiento | Alto con Receiver; Bajo con Invoker | Encapsula parámetros, almacena el estado y delega la ejecución al Receiver. |
| **Invoker** | Emisor y Detonador | Exclusivamente con la interfaz Command | Desencadena la orden de ejecución cuando ocurre un evento de sistema o usuario. |
| **Receiver** | Lógica de Negocio | Nulo con Invoker o Command | Contiene las rutinas efectivas para ejecutar el trabajo de dominio. |
| **Client** | Configurador y Ensamblador | Conoce las clases concretas | Instancia los componentes y establece las relaciones entre Receiver, Command e Invoker. |

## **Propósito y Justificación de Uso: ¿Qué Resuelve y Para Qué Sirve?**

La adopción del patrón Command está plenamente justificada en escenarios donde las invocaciones directas de métodos generan rigidez acoplada, duplicación de código o limitaciones en la gestión temporal de las operaciones. En aplicaciones con interfaces de usuario complejas, es frecuente que una misma acción de negocio —como guardar un documento o eliminar un registro— pueda ser iniciada desde múltiples puntos, incluyendo botones de barra de herramientas, menús desplegables o atajos de teclado. La invocación directa obligaría a cada componente de la interfaz a conocer la lógica del dominio o a duplicar código de llamadas. Al interponer el patrón Command, todos estos elementos gráficos se acoplan de forma exclusiva a una única abstracción de comando, eliminando la redundancia y reduciendo la complejidad del mantenimiento.

Además de desacoplar emisores y receptores, el patrón resuelve la necesidad de parametrizar objetos con operaciones en tiempo de ejecución. Esto permite configurar dinámicamente el comportamiento de un emisor alterando únicamente el comando asignado a su estado interno. Asimismo, la capacidad de diferir ejecuciones resulta crucial en sistemas distribuidos o de alto rendimiento; un comando configurado puede ser encolado en un gestor de tareas o enviado a través de la red hacia un proceso secundario, retrasando su ejecución hasta el momento óptimo sin perder la información de su contexto de creación. Finalmente, el patrón sirve como la piedra angular para implementar mecanismos robustos de control de transacciones e historial de operaciones, ofreciendo la infraestructura básica para revertir cambios de estado mediante procedimientos de deshacer y rehacer (*undo/redo*).

## **Aplicaciones Prácticas y Patrones Arquitectónicos Derivados**

En el ámbito de la arquitectura de software, el patrón Command no se limita a un esquema de diseño local, sino que se extiende hacia paradigmas organizacionales de mayor escala. En arquitecturas avanzadas como Clean Architecture o la Arquitectura Hexagonal, el patrón se manifiesta a través de los Casos de Uso o Servicios de Aplicación. Por ejemplo, en aplicaciones de gestión de datos deportivos, transacciones complejas como la creación de una entidad de jugador o el procesamiento de una planilla con estadísticas de partido son encapsuladas dentro de objetos de caso de uso. Esta estructuración garantiza que las capas externas de controlador o interfaz gráfica únicamente interactúen con la frontera del caso de uso, abstrayendo por completo el acceso a los repositorios y la lógica de dominio interna.

Otra aplicación fundamental se encuentra en la construcción de motores de historial para editores interactivos. Este comportamiento se logra mediante una arquitectura de doble pila, en la cual el sistema mantiene una pila de historial pasado para ejecuciones finalizadas y una pila de historial futuro para operaciones revertidas. Cada vez que el usuario realiza una modificación, el comando asociado ejecuta su método principal y se apila en el historial pasado, limpiando la pila futura debido a la invalidez de la rama previa. Cuando se solicita un deshacer, el comando superior de la pila pasada es desapilado, se ejecuta su rutina de reversión y se traslada a la pila futura. Del mismo modo, la acción de rehacer toma el comando de la pila futura, vuelve a invocar su ejecución y lo regresa al historial pasado, manteniendo la coherencia del estado.

A nivel de sistemas distribuidos, el patrón constituye la base conceptual de *Command Query Responsibility Segregation* (CQRS). En estas arquitecturas, las operaciones de modificación de estado se modelan estrictamente como comandos representados por objetos de datos inmutables que son procesados mediante un bus de comandos centralizado. De manera complementaria, en el patrón *Event Sourcing*, el estado actual de la aplicación no se persiste directamente, sino que se deduce mediante la reconstrucción cronológica de una secuencia almacenada de eventos y comandos procesados en el tiempo. Esta misma aproximación conceptual es la que sustenta las arquitecturas de gestión de estado en entornos frontend como Redux, donde las acciones enviadas al *store* son comandos serializados que expresan transformaciones explícitas del estado de la interfaz.

## **Paradigmas de Implementación: Enfoques Orientado a Objetos y Funcional**

La implementación del patrón Command adopta matices sustancialmente distintos según las capacidades del lenguaje de programación empleado. En lenguajes orientados a objetos con tipado estático como Java, se recurre a la definición formal de interfaces y clases concretas para representar cada acción. A continuación se ilustra una implementación representativa de este modelo aplicada a la manipulación de documentos de texto en **Java**:

```java
import java.util.Stack;

public interface ICommand {
    void execute();
    void undo();
}

public class TextDocument {
    private String content = "";

    public String getContent() {
        return content;
    }

    public void insertText(String text, int position) {
        content = new StringBuilder(content).insert(position, text).toString();
    }

    public void removeText(int position, int length) {
        content = new StringBuilder(content).delete(position, position + length).toString();
    }
}

public class InsertTextCommand implements ICommand {
    private final TextDocument document;
    private final String textToInsert;
    private final int position;

    public InsertTextCommand(TextDocument document, String text, int position) {
        this.document = document;
        this.textToInsert = text;
        this.position = position;
    }

    @Override
    public void execute() {
        document.insertText(textToInsert, position);
    }

    @Override
    public void undo() {
        document.removeText(position, textToInsert.length());
    }
}

public class DocumentEditor {
    private final Stack<ICommand> history = new Stack<>();

    public void executeCommand(ICommand command) {
        command.execute();
        history.push(command);
    }

    public void undoLast() {
        if (!history.isEmpty()) {
            ICommand command = history.pop();
            command.undo();
        }
    }
}
```

Asimismo, se puede implementar el mismo modelo de manera limpia en **Python**, aprovechando clases abstractas o dinámicas para estructurar el patrón orientado a objetos:

```python
from abc import ABC, abstractmethod

class ICommand(ABC):
    @abstractmethod
    def execute(self) -> None:
        pass

    @abstractmethod
    def undo(self) -> None:
        pass

class TextDocument:
    def __init__(self):
        self.content: str = ""

    def insert_text(self, text: str, position: int) -> None:
        self.content = self.content[:position] + text + self.content[position:]

    def remove_text(self, position: int, length: int) -> None:
        self.content = self.content[:position] + self.content[position + length:]

class InsertTextCommand(ICommand):
    def __init__(self, document: TextDocument, text_to_insert: str, position: int):
        self._document = document
        self._text_to_insert = text_to_insert
        self._position = position

    def execute(self) -> None:
        self._document.insert_text(self._text_to_insert, self._position)

    def undo(self) -> None:
        self._document.remove_text(self._position, len(self._text_to_insert))

class DocumentEditor:
    def __init__(self):
        self._history: list[ICommand] = []

    def execute_command(self, command: ICommand) -> None:
        command.execute()
        self._history.append(command)

    def undo_last(self) -> None:
        if self._history:
            command = self._history.pop()
            command.undo()
```

Por otro lado, la evolución de los lenguajes hacia paradigmas funcionales ha transformado la necesidad de crear jerarquías de clases extensas. En lenguajes que soportan funciones de primera clase y clausuras (*closures*) como JavaScript o Python, los comandos simples pueden expresarse mediante funciones de orden superior o lambdas que capturan las variables de su entorno sin requerir instancias dedicadas. Como observó Peter Norvig, en lenguajes dinámicos o funcionales, varios patrones de la GoF se simplifican o quedan implícitos en el propio lenguaje. Sin embargo, la estructura basada en clases conserva ventajas operativas insustituibles cuando la aplicación exige soporte de reversión (*undo*), inspección de metadatos o serialización de peticiones.

| Criterio de Comparación | Command Pattern | Strategy Pattern | Callback Function |
| :--- | :--- | :--- | :--- |
| **Intención Principal** | Encapsular una solicitud como un objeto para posponer, revertir o encolar su ejecución. | Intercambiar algoritmos o estrategias de procesamiento en tiempo de ejecución. | Pasar una función ejecutable como argumento para ser llamada tras completar un evento. |
| **Gestión de Estado** | Captura explícitamente parámetros y contexto dentro del objeto comando. | Habitualmente sin estado (*stateless*); los datos se reciben por parámetro. | Almacena variables locales mediante el mecanismo de clausura (*closure*). |
| **Soporte Undo/Redo** | Soporte nativo mediante la encapsulación del estado previo y rutinas de reversión. | No aplicable al propósito del patrón. | Difícil de gestionar; requiere lógica externa explícita. |
| **Estructura Requerida** | Clases dedicadas u objetos con interfaz de ejecución. | Jerarquía de clases de estrategia compartiendo una interfaz común. | Referencia a función o lambda sin clases adicionales. |

## **Temas Avanzados para el Estudio Posterior**

Para alcanzar una comprensión profunda del patrón Command en la ingeniería de software profesional, se requiere el análisis de variaciones sofisticadas que abordan problemas de escala, rendimiento y persistencia. Una de estas extensiones es el **MacroComando**, que integra el patrón *Composite* para permitir que una sola instancia de comando contenga y gestione una secuencia de subcomandos. Al ejecutar un MacroComando, las operaciones constitutivas se procesan secuencialmente, mientras que durante una operación de deshacer, los subcomandos se revierten en orden inverso, garantizando el cumplimiento estricto de las propiedades de atomicidad en transacciones compuestas.

En aplicaciones con interfaces altamente interactivas o de baja latencia, el concepto de **Comandos Optimistas** (*Optimistic Commands*) adquiere una relevancia crítica. En este esquema, el comando aplica inmediatamente las modificaciones en el estado local de la interfaz antes de recibir la confirmación de la red o del servidor. Si la llamada remota falla o es rechazada por el backend, la aplicación ejecuta automáticamente el método de deshacer del comando, restaurando el estado visual sin afectar la fluidez percibida por el usuario.

Asimismo, la **Coalescencia de Comandos** (*Command Coalescing*) resuelve los problemas de consumo desmedido de memoria producidos por la generación continua de comandos ante eventos de alta frecuencia, tales como el arrastre de elementos en pantalla o la entrada rápida de texto. Mediante la coalescencia, múltiples comandos consecutivos del mismo tipo ocurridos dentro de una ventana de tiempo predefinida se fusionan en un único comando consolidado. Finalmente, la **Persistencia y Serialización** de comandos extiende la utilidad del patrón hacia la tolerancia a fallos y los sistemas distribuidos, permitiendo convertir comandos en formatos como JSON o flujos de bytes para almacenarlos en registros de auditoría o transmitirlos a través de colas de mensajes en arquitecturas orientadas a eventos.

## **Conclusiones y Consideraciones Arquitectónicas**

El patrón Command constituye un pilar esencial en el diseño de arquitecturas de software flexibles y desacopladas. Al convertir las solicitudes operativas en objetos manipulables de primera clase, trasciende la mera abstracción orientada a objetos para convertirse en la base de sistemas de gestión de estado, motores de historial, canalizaciones asíncronas y marcos arquitectónicos como CQRS y Event Sourcing.

No obstante, la decisión de adoptar el patrón debe sopesarse cuidadosamente frente a los costos de complejidad estructural. La introducción de múltiples clases concretas para operaciones simples puede generar una sobrecarga de mantenimiento e indirección innecesaria si el sistema no requiere diferir la ejecución, encolar tareas ni mantener un historial de transacciones. Por consiguiente, la implementación del patrón Command debe reservarse para dominios donde la flexibilidad temporal, el desacoplamiento estricto y la capacidad de reversión agreguen un valor técnico justificable.

## **Cómo lo aplica este proyecto (la CLI de StatsPro)**

> **Aviso (2026-10-31):** la CLI se retira en la **US-105**. Esta sección describe cómo quedó aplicada hasta entonces; la teoría de arriba sigue valiendo. En la GUI el mismo objetivo (agregar una acción sin tocar las demás) lo cumple la convención "una pantalla por archivo" registrada en la tabla de rutas de `app.py`.

Todo lo anterior es la teoría general del patrón. En este proyecto se usa una variante **funcional y liviana**, la tercera columna de la tabla de arriba
(*"referencia a función sin clases adicionales"*), apoyada en `argparse`. No hay una clase por comando: cada comando es una **función `ejecutar`** y el parser
`argparse` cumple el rol de *Invoker*.

| Rol del patrón | En el proyecto |
| :--- | :--- |
| **Command** (contrato) | La firma común `ejecutar(args: argparse.Namespace, ...) -> None` |
| **ConcreteCommand** | Un archivo por acción en `src/infraestructura/ui/cli/commands/` (`club_add.py`, `jugador_link.py`, `competencia_inscribir.py`, ...) |
| **Receiver** (quien hace el trabajo real) | El caso de uso (`CrearClubUseCase`, ...) que el comando invoca |
| **Invoker** | El parser de `argparse`: `parse_args()` decide qué comando corresponde y `main()` lo ejecuta |
| **Client / registro** | `construir_parser()` en `src/main.py`, que asocia cada subcomando con su función mediante `set_defaults(func=...)` |

**Cómo se registra un comando** (sin ningún `if/elif`):

```python
parser_club_add = club_subparsers.add_parser("add", help="Crea un club nuevo")
parser_club_add.add_argument("--nombre", required=True)
parser_club_add.set_defaults(func=club_add.ejecutar)   # <- acá se "ata" el comando a su función

# main():
args = parser.parse_args()
args.func(args)          # ejecuta el comando que corresponda, sea cual sea
```

**Qué se gana:** agregar un comando nuevo es (1) crear su archivo en `commands/` y (2) sumar su bloque en `construir_parser()`. No se toca ningún otro comando
(criterio de aceptación AC1 de la US-106).

**Lo que este proyecto NO usa del patrón** (por ahora): *undo/redo*, colas de comandos, macro-comandos ni historial. Como advierten las conclusiones de arriba, esos costos
no se justifican mientras no haga falta diferir, encolar ni revertir acciones.

**Manejo de errores centralizado:** los comandos no atrapan los errores de negocio: los dejan subir hasta `main()`, que los captura con un único `except ErrorDeDominio` y los muestra
como `Error: ...` en stderr con código de salida 1. Más contexto en [04-arquitectura.md](04-arquitectura.md) (sección 10) y en el [RUNBOOK](../../RUNBOOK.md).

#### **Fuentes Consultadas**

1. **Command** - Refactoring.Guru: [https://refactoring.guru/design-patterns/command](https://refactoring.guru/design-patterns/command)
2. **Command Pattern** - Patterns.dev: [https://www.patterns.dev/vanilla/command-pattern/](https://www.patterns.dev/vanilla/command-pattern/)
3. **The Command Design Pattern** - UMLBoard: [https://www.umlboard.com/design-patterns/command.html](https://www.umlboard.com/design-patterns/command.html)
4. **Command in C++ / Design Patterns** - Refactoring.Guru: [https://refactoring.guru/design-patterns/command/cpp/example](https://refactoring.guru/design-patterns/command/cpp/example)
5. **Command in C# / Design Patterns** - Refactoring.Guru: [https://refactoring.guru/design-patterns/command/csharp/example](https://refactoring.guru/design-patterns/command/csharp/example)
6. **Configuración de Cuaderno DSI**, Documentación de Arquitectura de Software
7. **Why Patterns Failed and Why You Should Care** - Hacker News: [https://news.ycombinator.com/item?id=18153074](https://news.ycombinator.com/item?id=18153074)
