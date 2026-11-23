from abc import ABC, abstractmethod

from dominio.entidades.competencia import (
    Categoria,
    Competencia,
    Inscripcion,
    JugadorListaBuenaFe,
    ListaBuenaFe,
)


class CompetenciaRepositorio(ABC):
    "Maneja competencia, categoria, inscripcion, listaBuenaFe y jugadorListaBuenaFe"

    @abstractmethod
    def guardar_competencia(self, compe: Competencia) -> Competencia | None:
        "Registra una Competencia"
        pass

    @abstractmethod
    def guardar_competencia_con_categorias(self, compe: Competencia, idCategorias: list[int]) -> Competencia | None:
        "Registra una Competencia y las categorias que juega en una unica transaccion atomica (US-107)"
        pass

    @abstractmethod
    def buscar_competencia_por_id(self, idCompetencia: int) -> Competencia | None:
        "Busca una Competencia por id"
        pass

    @abstractmethod
    def obtener_todas_competencias(self) -> list[Competencia]:
        "Devuelve todas las competencias existentes"
        pass

    @abstractmethod
    def guardar_categoria(self, cat: Categoria) -> Categoria | None:
        "Registra una Categoria"
        pass

    @abstractmethod
    def obtener_categorias(self) -> list[Categoria]:
        "Devuelve todas las categorias existentes"
        pass

    @abstractmethod
    def habilitar_categoria(self, idCompetencia: int, idCategoria: int) -> bool:
        "Habilita una categoria en una competencia. Devuelve False si ya estaba habilitada o si fallo"
        pass

    @abstractmethod
    def obtener_categorias_de_competencia(self, idCompetencia: int) -> list[Categoria]:
        "Devuelve las categorias que juega una competencia"
        pass

    @abstractmethod
    def quitar_categoria(self, idCompetencia: int, idCategoria: int) -> bool:
        "Quita una categoria de una competencia. Devuelve False si no estaba habilitada o si fallo"
        pass

    @abstractmethod
    def tiene_inscripciones(self, idCompetencia: int, idCategoria: int) -> bool:
        "Indica si hay clubes inscriptos en esa competencia y categoria"
        pass

    @abstractmethod
    def guardar_inscripcion(self, inscripcion: Inscripcion) -> Inscripcion | None:
        "Guarda una inscripcion"
        pass

    @abstractmethod
    def inscribir_con_lista(
        self, inscripcion: Inscripcion, fecha_presentacion: str
    ) -> tuple[Inscripcion, ListaBuenaFe] | None:
        "Guarda una inscripcion y su lista de buena fe vacia (1:1) en una unica transaccion atomica"
        pass

    @abstractmethod
    def buscar_inscripcion_por_id(self, idInscripcion: int) -> Inscripcion | None:
        "Devuelve informacion de una inscripcion por ID"
        pass

    @abstractmethod
    def obtener_inscripciones_por_club(self, idClub: int) -> list[Inscripcion]:
        "Devuelve todas las inscripciones de un club"
        pass

    @abstractmethod
    def guardar_lista_buena_fe(self, listaBF: ListaBuenaFe) -> ListaBuenaFe | None:
        "Genera una lista de buena fe vacia"
        pass

    @abstractmethod
    def obtener_lista_por_inscripcion(self, idInscripcion: int) -> ListaBuenaFe | None:
        "Obtiene informacion de la lista de buena fe de una inscripcion"
        pass

    @abstractmethod
    def agregar_jugador_lista(self, idJugador: int, idListaBuenaFe: int) -> JugadorListaBuenaFe | None:
        "Agrega un jugador a una lista de buena fe"
        pass

    @abstractmethod
    def obtener_jugadores_lista(self, idListaBuenaFe: int) -> list[JugadorListaBuenaFe]:
        "Obtiene todos los jugadores de una lista de buena fe"
        pass

    @abstractmethod
    def quitar_jugador_lista(self, idJugador: int, idListaBuenaFe: int) -> bool:
        "Quita a un jugador de una lista de buena fe. Devuelve True si lo quito, False si no estaba o si fallo"
        pass

    @abstractmethod
    def competencia_tiene_inscripciones(self, idCompetencia: int) -> bool:
        "Indica si la competencia tiene al menos un club inscripto en alguna categoria"
        pass

    @abstractmethod
    def competencia_tiene_partidos(self, idCompetencia: int) -> bool:
        "Indica si la competencia tiene al menos un partido cargado"
        pass

    @abstractmethod
    def eliminar_competencia(self, idCompetencia: int) -> bool:
        "Elimina una competencia existente. Devuelve True si se elimino, False si no existia o fallo"
        pass

    @abstractmethod
    def categoria_en_uso(self, idCategoria: int) -> bool:
        "Indica si la categoria esta habilitada en alguna competencia o tiene inscripciones"
        pass

    @abstractmethod
    def eliminar_categoria(self, idCategoria: int) -> bool:
        "Elimina una categoria del catalogo. Devuelve True si se elimino, False si no existia o fallo"
        pass

    @abstractmethod
    def inscripcion_tiene_partidos(self, idInscripcion: int) -> bool:
        "Indica si el club de la inscripcion tiene partidos cargados en esa competencia"
        pass

    @abstractmethod
    def eliminar_inscripcion(self, idInscripcion: int) -> bool:
        "Elimina una inscripcion y en cascada su lista de buena fe 1:1"
        pass

    @abstractmethod
    def vaciar_lista_buena_fe(self, idListaBuenaFe: int) -> bool:
        "Quita todos los jugadores habilitados de una lista de buena fe"
        pass
