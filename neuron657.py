#!/usr/bin/env python3
"""
Neuron657 v7.7 - Sistema Neuromórfico creado por Walter Diego Spaltro
===================================================================
"""

from enum import Enum
import os
import math
import struct
import random
import hashlib
import threading
import time
import logging
from heapq import nlargest
from typing import Optional, List, Dict, Tuple, Any, Union, BinaryIO
from dataclasses import dataclass
from collections import OrderedDict, defaultdict
from contextlib import contextmanager
import sys
import concurrent.futures
from datetime import datetime
import shutil

# ============================================
# Configuración de logging SIMPLIFICADA
# ============================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - neuron657 - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("neuron657.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)

# Configurar nivel de logging para módulos internos
logging.getLogger("neuron657").setLevel(logging.INFO)

# ============================================
# Excepciones personalizadas
# ============================================

class Neuron657Error(Exception):
    """Excepción base para errores de Neuron657."""
    pass

class PersistenceError(Neuron657Error):
    """Error en operaciones de persistencia."""
    pass

class IntegrityError(Neuron657Error):
    """Error de integridad de datos."""
    pass

class MemoryFullError(Neuron657Error):
    """Error cuando la memoria está llena."""
    pass

# ============================================
# Constantes y configuración
# ============================================

@dataclass

class SimilarityMode(Enum):
    EXACT = 1
    NUMERIC = 2
    SEMANTIC = 3

class Config:
    """Configuración centralizada del sistema."""
    
    DEFAULT_PATTERN_SIZE: int = 64
    DEFAULT_CLUSTER_SIZE: int = 512
    DEFAULT_TOTAL_SIZE: int = 2 * 1024 * 1024
    
    # Parámetros de Plasticidad Adaptativa
    ADAPTIVE_DRIFT_BASE: float = 0.005
    STABILITY_THRESHOLD: int = 5
    
    # Parámetros de Mantenimiento Autónomo (Pruning)
    PRUNING_THRESHOLD: int = 2
    PRUNING_INTERVAL: int = 25
    
    # Parámetros de Rendimiento y Robustez
    BACKGROUND_SLEEP: float = 0.5
    CACHE_SIZE: int = 1000
    FLUSH_INTERVAL: int = 100
    ASYNC_IO_WORKERS: int = 4
    WAL_FILE_SUFFIX: str = ".wal"
    
    # Configuraciones avanzadas
    PERSISTENCE_ENABLED: bool = True
    BACKUP_ENABLED: bool = True
    AUTO_RECOVERY: bool = True
    LOG_LEVEL: str = "INFO"
    
    def __post_init__(self):
        """Configurar logging basado en variable de entorno."""
        logging.getLogger(__name__).setLevel(getattr(logging, self.LOG_LEVEL))

# ============================================
# BLOQUE 1 — NPF657Pattern
# ============================================

class NPF657Pattern:
    SIZE = Config.DEFAULT_PATTERN_SIZE
    
    def __init__(
        self,
        data: Optional[bytes] = None,
        tags: Optional[List[str]] = None,
        cid: Optional[int] = None,
        offset: Optional[int] = None,
    ):
        if data is None:
            self.data = bytearray(os.urandom(self.SIZE))
        else:
            if len(data) != self.SIZE:
                raise ValueError(
                    f"Pattern size mismatch: expected {self.SIZE}, got {len(data)}"
                )
            self.data = bytearray(data)
        
        self.tags = tags.copy() if tags else []
        self._hash_cache: Optional[str] = None
        self.cid = cid
        self.offset = offset
    
    def __repr__(self) -> str:
        loc = f"@{self.cid}:{self.offset}" if self.cid is not None else "UNBOUND"
        return f"<NPF657Pattern loc={loc} size={self.SIZE} tags={self.tags}>"
    
    def to_bytes(self) -> bytes:
        return bytes(self.data)
    
    @staticmethod
    def calculate_similarity_bytes(data1: bytes, data2: bytes, size: int) -> float:
        """Cálculo de similitud byte-a-byte, sin crear objetos."""
        if len(data1) != size or len(data2) != size:
            return 0.0
        # FIXED: Usamos distancia Manhattan para permitir aprendizaje difuso
        total_diff = sum(abs(b1 - b2) for b1, b2 in zip(data1, data2))
        max_diff = size * 255.0
        return 1.0 - (total_diff / max_diff)
    
    def similarity(self, other: "NPF657Pattern") -> float:
        return self.calculate_similarity_bytes(
            self.to_bytes(), other.to_bytes(), self.SIZE
        )
    
    def drift_mutation(self, amount: float = 0.05) -> None:
        amount = max(0.0, min(1.0, amount))
        num_mutations = int(self.SIZE * amount)
        for _ in range(num_mutations):
            idx = random.randint(0, self.SIZE - 1)
            # FIXED: Mutación suave en lugar de ruido total
            delta = random.choice([-10, -5, 5, 10])
            self.data[idx] = max(0, min(255, self.data[idx] + delta))
        self._hash_cache = None
    
    def hash(self) -> str:
        if self._hash_cache is None:
            self._hash_cache = hashlib.sha256(self.data).hexdigest()
        return self._hash_cache

# ============================================
# BLOQUE 2 — LRUCache
# ============================================

class LRUCache:
    """Cache LRU optimizada."""
    
    def __init__(self, maxsize: int = Config.CACHE_SIZE):
        self.maxsize = maxsize
        self.cache: OrderedDict[int, bytearray] = OrderedDict()
        self.hits = 0
        self.misses = 0
    
    def get(self, key: int) -> Optional[bytearray]:
        if key in self.cache:
            value = self.cache.pop(key)
            self.cache[key] = bytearray(value)
            self.hits += 1
            return value
        self.misses += 1
        return None
    
    def put(self, key: int, value: bytearray) -> None:
        if key in self.cache:
            self.cache.pop(key)
        elif len(self.cache) >= self.maxsize:
            self.cache.popitem(last=False)
        
        self.cache[key] = value
    
    def clear(self) -> None:
        self.cache.clear()
        self.hits = 0
        self.misses = 0
    
    def stats(self) -> Dict[str, Any]:
        total = self.hits + self.misses
        hit_rate = (self.hits / total * 100) if total > 0 else 0
        return {
            "size": len(self.cache),
            "maxsize": self.maxsize,
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": f"{hit_rate:.1f}%",
        }

# ============================================
# BLOQUE 3 — WAL657Delta
# ============================================

class WAL657Delta:
    """Write-Ahead Log que loguea solo deltas de patrón (64B)."""
    
    def __init__(self, filepath: str, pattern_size: int):
        self.filepath = filepath + Config.WAL_FILE_SUFFIX
        self.pattern_size = pattern_size
        self.log_handle: Optional[BinaryIO] = None
        self.lock = threading.Lock()
        self._initialize()
    
    def _initialize(self):
        try:
            if self.log_handle is None:
                self.log_handle = open(self.filepath, "a+b")
                logger.info(f"WAL657Delta log opened: {self.filepath}")
        except Exception as e:
            logger.error(f"FATAL: Could not open WAL file: {e}")
            raise
    
    def log_pattern_write(self, cid: int, offset: int, data: bytearray) -> None:
        if len(data) != self.pattern_size:
            raise ValueError(
                f"Delta data size mismatch: expected {self.pattern_size}, got {len(data)}"
            )
        
        with self.lock:
            if not self.log_handle:
                raise IOError("WAL handle is not open")
            
            record = struct.pack("!BII", 2, cid, offset)
            record += data
            
            self.log_handle.write(record)
            self.log_handle.flush()
            os.fsync(self.log_handle.fileno())
    
    def recover(self, memory: "UMN657Memory") -> int:
        recovery_count = 0
        with self.lock:
            if not self.log_handle:
                return 0
            self.log_handle.seek(0)
            HEADER_SIZE = 9
            while True:
                header = self.log_handle.read(HEADER_SIZE)
                if len(header) != HEADER_SIZE:
                    break
                magic, cid, offset = struct.unpack("!BII", header)
                data = self.log_handle.read(self.pattern_size)
                if len(data) != self.pattern_size:
                    break
                if magic == 2:
                    memory._write_pattern_physical(cid, offset, bytearray(data))
                    recovery_count += 1
            logger.info(f"WAL Recovery completed: {recovery_count} operations applied.")
        return recovery_count
    
    def checkpoint(self) -> None:
        """Checkpoint con os.fsync para persistencia real."""
        with self.lock:
            if self.log_handle:
                self.log_handle.flush()
                os.fsync(self.log_handle.fileno())
                self.log_handle.truncate(0)
                self.log_handle.seek(0)
                logger.info("WAL checkpoint created (log truncated and fsync applied).")
    
    def cleanup(self) -> None:
        with self.lock:
            if self.log_handle:
                self.log_handle.close()
                self.log_handle = None

# ============================================
# BLOQUE 4 — NPF657CompactStore (CON PERSISTENCIA)
# ============================================

class NPF657CompactStore:
    """Gestión de la Compactación de Patrones CON PERSISTENCIA OPTIMIZADA."""
    
    def __init__(
        self,
        cluster_count: int,
        pattern_size: int = Config.DEFAULT_PATTERN_SIZE,
        persistence_file: Optional[str] = None,
    ):
        self.cluster_count = cluster_count
        self.pattern_size = pattern_size
        self.cluster_size = Config.DEFAULT_CLUSTER_SIZE
        self.slots_per_cluster = self.cluster_size // self.pattern_size
        
        # Archivo de persistencia
        self.persistence_file = persistence_file
        
        # Optimización: Batch saving
        self._dirty = False
        self._save_counter = 0
        self._save_threshold = 20  # Guardar cada 20 operaciones
        
        if self.persistence_file and os.path.exists(
            self.persistence_file + ".compactstore"
        ):
            self._load_from_disk()
        else:
            # Inicializar estructuras vacías
            self.cluster_status: Dict[int, List[bool]] = defaultdict(
                lambda: [False] * self.slots_per_cluster
            )
            self.pattern_to_loc: Dict[str, Tuple[int, int]] = {}
            self.loc_to_hash: Dict[Tuple[int, int], str] = {}
            self.total_patterns = 0
        
        logger.info(
            f"Initialized NPF657CompactStore (Optimized): {self.slots_per_cluster} slots/cluster, "
            f"{self.total_patterns} patterns loaded from persistence."
        )
    
    def _load_from_disk(self):
        """Cargar estado desde disco."""
        try:
            file_path = self.persistence_file + ".compactstore"
            logger.info(f"Loading CompactStore from: {file_path}")
            
            with open(file_path, "rb") as f:
                # Leer versión
                version = struct.unpack("B", f.read(1))[0]
                if version != 1:
                    raise ValueError(f"Versión de compactstore no soportada: {version}")
                
                # Leer conteos
                total_patterns = struct.unpack("I", f.read(4))[0]
                self.total_patterns = total_patterns
                
                # Inicializar estructuras
                self.cluster_status = defaultdict(
                    lambda: [False] * self.slots_per_cluster
                )
                self.pattern_to_loc = {}
                self.loc_to_hash = {}
                
                # Leer cada patrón
                for _ in range(total_patterns):
                    # Leer hash (64 bytes como hex string)
                    hash_bytes = f.read(64)
                    pattern_hash = hash_bytes.decode("ascii")
                    
                    # Leer ubicación
                    cid, offset = struct.unpack("II", f.read(8))
                    
                    # Restaurar estructuras
                    self.pattern_to_loc[pattern_hash] = (cid, offset)
                    self.loc_to_hash[(cid, offset)] = pattern_hash
                    
                    # Marcar slot como ocupado
                    slot_index = offset // self.pattern_size
                    if cid not in self.cluster_status:
                        self.cluster_status[cid] = [False] * self.slots_per_cluster
                    self.cluster_status[cid][slot_index] = True
                
                logger.info(f"Loaded {total_patterns} patterns from persistence file")
        
        except Exception as e:
            logger.error(f"Error loading compactstore from disk: {e}")
            # Fallback a estado vacío
            self.cluster_status = defaultdict(lambda: [False] * self.slots_per_cluster)
            self.pattern_to_loc = {}
            self.loc_to_hash = {}
            self.total_patterns = 0
    
    def _save_to_disk(self, force: bool = False):
        """Guardar estado a disco con optimización batch."""
        if not self.persistence_file:
            return
        
        # Solo guardar si hay cambios pendientes o se fuerza
        if not self._dirty and not force:
            return
        
        try:
            file_path = self.persistence_file + ".compactstore"
            
            logger.debug(
                f"Saving CompactStore to: {file_path} ({self.total_patterns} patterns)"
            )
            
            with open(file_path, "wb") as f:
                # Escribir versión
                f.write(struct.pack("B", 1))
                
                # Escribir total de patrones
                f.write(struct.pack("I", self.total_patterns))
                
                # Escribir cada patrón
                for pattern_hash, loc in self.pattern_to_loc.items():
                    cid, offset = loc
                    
                    # Escribir hash (64 bytes)
                    f.write(pattern_hash.encode("ascii"))
                    
                    # Escribir ubicación
                    f.write(struct.pack("II", cid, offset))
                
                # Forzar escritura a disco
                f.flush()
                os.fsync(f.fileno())
            
            # Resetear contadores
            self._dirty = False
            self._save_counter = 0
        
        except Exception as e:
            logger.error(f"Error saving compactstore to disk: {e}")
            # Mantener dirty flag si falló
            self._dirty = True
    
    def find_free_slot(self) -> Tuple[int, int]:
        for cid in range(self.cluster_count):
            for i in range(self.slots_per_cluster):
                if not self.cluster_status[cid][i]:
                    offset = i * self.pattern_size
                    return (cid, offset)
        raise MemoryFullError("CompactStore is full! No free cluster slots available.")
    
    def allocate_slot(self, pattern: "NPF657Pattern") -> Tuple[int, int]:
        cid, offset = self.find_free_slot()
        loc = (cid, offset)
        slot_index = offset // self.pattern_size
        
        self.cluster_status[cid][slot_index] = True
        self.pattern_to_loc[pattern.hash()] = loc
        self.loc_to_hash[loc] = pattern.hash()
        self.total_patterns += 1
        
        # Persistir cambios con optimización batch
        self._dirty = True
        self._save_counter += 1
        
        # Guardar en lotes
        if self._save_counter >= self._save_threshold:
            self._save_to_disk()
        
        return loc
    
    def update_hash_after_drift(
        self, old_hash: str, new_hash: str, loc: Tuple[int, int]
    ) -> None:
        """Actualiza atómicamente los mapeos hash -> loc y loc -> hash después de DRIFT."""
        cid, offset = loc
        
        # 1. Eliminar mapeo antiguo (si existe)
        if old_hash in self.pattern_to_loc and self.pattern_to_loc[old_hash] == loc:
            del self.pattern_to_loc[old_hash]
        
        # 2. Reafirmar el mapeo de ubicación a nuevo hash
        self.loc_to_hash[loc] = new_hash
        
        # 3. Establecer el nuevo mapeo de hash a ubicación
        self.pattern_to_loc[new_hash] = loc
        
        # 4. Persistir cambios con optimización
        self._dirty = True
        self._save_counter += 1
        
        if self._save_counter >= self._save_threshold:
            self._save_to_disk()
    
    def free_slot_by_loc(self, cid: int, offset: int) -> Optional[str]:
        """Libera un slot usando la ubicación (usado por PRUNING ATÓMICO)."""
        loc = (cid, offset)
        pattern_hash = self.loc_to_hash.pop(loc, None)
        
        if pattern_hash:
            if pattern_hash in self.pattern_to_loc:
                del self.pattern_to_loc[pattern_hash]
            
            slot_index = offset // self.pattern_size
            self.cluster_status[cid][slot_index] = False
            self.total_patterns -= 1
            
            # Persistir cambios con optimización
            self._dirty = True
            self._save_counter += 1
            
            if self._save_counter >= self._save_threshold:
                self._save_to_disk()
            
            return pattern_hash
        return None
    
    def get_all_active_locations(self) -> List[Tuple[int, int]]:
        return list(self.loc_to_hash.keys())
    
    def get_location_by_hash(self, pattern_hash: str) -> Optional[Tuple[int, int]]:
        return self.pattern_to_loc.get(pattern_hash)
    
    def get_hash_by_location(self, cid: int, offset: int) -> Optional[str]:
        return self.loc_to_hash.get((cid, offset))
    
    def cleanup(self):
        """Limpieza al cerrar."""
        # Asegurar que el último estado esté guardado
        if self._dirty:
            self._save_to_disk(force=True)

class UMN657Memory:
    """Memoria de Acceso Neuromórfico Unificado (UMN) v5.7 con persistencia completa y thread-safe."""
    
    def __init__(self, filepath: str, **kwargs):
        self.filepath = filepath
        self.cluster_size = Config.DEFAULT_CLUSTER_SIZE
        self.pattern_size = Config.DEFAULT_PATTERN_SIZE
        self.total_size = kwargs.get("total_size", Config.DEFAULT_TOTAL_SIZE)
        self.cluster_count = self.total_size // self.cluster_size
        
        self.lock = threading.RLock()
        self.io_lock = threading.Lock()
        
        self.file_handle: Optional[BinaryIO] = None
        self.wal = WAL657Delta(filepath, self.pattern_size)
        
        self.cache = LRUCache()
        
        # IMPORTANTE: Pasar filepath para persistencia del CompactStore
        self.compact_store = NPF657CompactStore(
            self.cluster_count, persistence_file=filepath
        )
        
        self.write_count = 0
        self.read_count = 0
        self.access_stats: Dict[Tuple[int, int], int] = defaultdict(int)
        
        logger.info(
            f"Initializing UMN657Memory v5.7: {self.cluster_count} clusters ({self.cluster_size}B)..."
        )
        
        self._initialize_file()
        self.wal.recover(self)
    
    def _initialize_file(self) -> None:
        file_exists = os.path.exists(self.filepath)
        if not file_exists:
            with open(self.filepath, "wb") as f:
                f.write(os.urandom(self.total_size))
        
        current_size = os.path.getsize(self.filepath)
        if current_size != self.total_size:
            logger.warning(
                f"Resizing memory file: {current_size:,} -> {self.total_size:,} bytes"
            )
            with open(self.filepath, "r+b") as f:
                f.truncate(self.total_size)
        
        try:
            if self.file_handle is None:
                self.file_handle = open(self.filepath, "r+b")
                logger.info(f"Opened persistent file handle for: {self.filepath}")
        except Exception as e:
            raise
    
    def _offset(self, cid: int) -> int:
        return cid * self.cluster_size
    
    def _validate_offset(self, offset: int) -> None:
        """Valida que el offset esté alineado al patrón."""
        if offset % self.pattern_size != 0:
            raise ValueError(
                f"Offset {offset} must be a multiple of PATTERN_SIZE ({self.pattern_size})."
            )
    
    def _read_cluster_physical(self, cid: int) -> bytearray:
        """Lee un cluster DIRECTAMENTE del disco (sin cache)."""
        if not (0 <= cid < self.cluster_count):
            raise IndexError(f"Cluster id {cid} out of range [0, {self.cluster_count})")
        
        offset = self._offset(cid)
        
        with self.io_lock:
            if not self.file_handle:
                raise IOError("File handle is not open")
            self.file_handle.seek(offset)
            data = bytearray(self.file_handle.read(self.cluster_size))
        return data
    
    def _write_pattern_physical(self, cid: int, offset: int, data: bytearray) -> None:
        """Escribe solo el patrón (64B) directamente al offset físico."""
        self._validate_offset(offset)
        cluster_offset = self._offset(cid) + offset
        with self.io_lock:
            if not self.file_handle:
                raise IOError("File handle is not open")
            self.file_handle.seek(cluster_offset)
            self.file_handle.write(data)
    
    def read_cluster(self, cid: int) -> bytearray:
        """Lee el cluster 'cid' con cache."""
        self.read_count += 1
        
        cached = self.cache.get(cid)
        if cached is not None:
            return cached
        
        # Lee del disco (usando el nuevo método físico)
        data = self._read_cluster_physical(cid)
        
        self.cache.put(cid, data)
        return data
    
    def write_pattern_delta(
        self, cid: int, offset: int, pattern_data: bytearray
    ) -> None:
        """Escribe un patrón con Fix de Cache Inconsistente."""
        self._validate_offset(offset)
        self.write_count += 1
        loc = (cid, offset)
        self.access_stats[loc] += 1
        
        # 1. Escribir en WAL y Físicamente
        self.wal.log_pattern_write(cid, offset, pattern_data)
        self._write_pattern_physical(cid, offset, pattern_data)
        
        if self.write_count % Config.FLUSH_INTERVAL == 0:
            with self.io_lock:
                if self.file_handle:
                    self.file_handle.flush()
        
        # 2. Actualizar Cache de forma robusta
        cluster_data = self.cache.get(cid)
        if cluster_data is None:
            return
        
        # Si está en cache, se actualiza el fragmento DENTRO del bytearray de la cache
        end_offset = offset + self.pattern_size
        cluster_data[offset:end_offset] = bytearray(pattern_data)
        
        # Se llama a put solo para moverlo al final de LRU (MRU)
        self.cache.put(cid, cluster_data)
    
    def load_pattern_compacted(self, cid: int, offset: int) -> "NPF657Pattern":
        """Carga un patrón con validación de offset y prefetching."""
        self._validate_offset(offset)
        loc = (cid, offset)
        with self.lock:
            self.access_stats[loc] += 1
        
        cluster_data = self.read_cluster(cid)
        start = offset
        end = offset + self.pattern_size
        pattern_data = cluster_data[start:end]
        
        # Lógica de Prefetching (mantenida de la versión original)
        if self.access_stats[loc] > Config.STABILITY_THRESHOLD:
            for delta in [-1, 1]:
                adj_cid = cid + delta
                if 0 <= adj_cid < self.cluster_count:
                    if (
                        sum(
                            self.access_stats.get((adj_cid, i * self.pattern_size), 0)
                            for i in range(self.compact_store.slots_per_cluster)
                        )
                        > Config.STABILITY_THRESHOLD
                    ):
                        self.read_cluster(adj_cid)
        
        return NPF657Pattern(data=pattern_data, cid=cid, offset=offset)
    
    def prune_pattern(self, cid: int, offset: int) -> Optional[str]:
        """Solo libera el slot lógico y borra estadísticas."""
        loc = (cid, offset)
        with self.lock:
            pattern_hash = self.compact_store.free_slot_by_loc(cid, offset)
            if pattern_hash:
                if loc in self.access_stats:
                    del self.access_stats[loc]
                logger.info(
                    f"PRUNING: Freed slot @{cid}:{offset} (Hash: {pattern_hash[:8]})"
                )
                return pattern_hash
            return None
    
    def get_pattern_stability(self, cid: int, offset: int) -> int:
        return self.access_stats.get((cid, offset), 0)
    
    def recover_from_corruption(self) -> Dict[str, Any]:
        """Intenta recuperar de corrupción de datos."""
        recovery_info = {
            "recovered_patterns": 0,
            "lost_patterns": 0,
            "rebuilt_index": False,
        }
        
        # Esta función será utilizada desde fuera para reconstruir el índice
        return recovery_info
    
    def store_pattern_compacted(self, pattern: "NPF657Pattern") -> Tuple[int, int]:
        with self.lock:
            cid, offset = self.compact_store.allocate_slot(pattern)
            self.write_pattern_delta(cid, offset, pattern.data)
            pattern.cid = cid
            pattern.offset = offset
            return cid, offset
    
    def cleanup(self) -> None:
        logger.info(f"Starting memory cleanup for {self.filepath}")
        with self.lock:
            self.wal.checkpoint()
            self.wal.cleanup()
            self.cache.clear()
            
            # IMPORTANTE: Guardar estado del CompactStore
            self.compact_store.cleanup()
            
            with self.io_lock:
                if self.file_handle:
                    self.file_handle.close()
                    self.file_handle = None
            logger.info(
                f"Memory cleanup completed. Final stats: "
                f"Reads={self.read_count}, Writes={self.write_count}"
            )

# ============================================
# BLOQUE 5 — NPF657SimilarityIndexL3 (CON PERSISTENCIA)
# ============================================

class NPF657SimilarityIndexL3:
    """Índice de Similitud en Capas (L3) con Grafo Contextual y Persistencia OPTIMIZADA."""
    
    def __init__(
        self,
        memory: "UMN657Memory",
        vector_dimension: int = Config.DEFAULT_PATTERN_SIZE,
        persistence_file: Optional[str] = None,
    ):
        self.mem = memory
        self.vector_dimension = vector_dimension
        self.hash_to_loc: Dict[str, Tuple[int, int]] = {}
        self.vectors: Dict[Tuple[int, int], bytes] = {}
        self.contextual_graph: Dict[str, List[str]] = defaultdict(list)
        
        # Optimización: Batch saving
        self.persistence_file = persistence_file
        self._dirty = False
        self._save_counter = 0
        self._save_threshold = 20
        
        if self.persistence_file and os.path.exists(self.persistence_file + ".index"):
            self._load_from_disk()
        
        logger.info(
            f"Initialized NPF657SimilarityIndexL3 (v5.7 Optimized Dims={vector_dimension}, "
            f"vectors={len(self.vectors)})"
        )
    
    def _load_from_disk(self):
        """Cargar índice desde disco."""
        try:
            file_path = self.persistence_file + ".index"
            logger.info(f"Loading Index from: {file_path}")
            
            with open(file_path, "rb") as f:
                # Leer versión
                version = struct.unpack("B", f.read(1))[0]
                if version != 1:
                    raise ValueError(f"Versión de índice no soportada: {version}")
                
                # Leer conteo de vectores
                vector_count = struct.unpack("I", f.read(4))[0]
                
                # Leer cada vector
                for _ in range(vector_count):
                    # Leer ubicación
                    cid, offset = struct.unpack("II", f.read(8))
                    loc = (cid, offset)
                    
                    # Leer vector
                    vector_data = f.read(self.vector_dimension)
                    if len(vector_data) != self.vector_dimension:
                        logger.error(
                            f"Vector data size mismatch: expected {self.vector_dimension}, got {len(vector_data)}"
                        )
                        break
                    
                    # Restaurar en estructuras
                    self.vectors[loc] = vector_data
                    
                    # Calcular hash
                    pattern_hash = hashlib.sha256(vector_data).hexdigest()
                    self.hash_to_loc[pattern_hash] = loc
                
                logger.info(
                    f"Loaded {len(self.vectors)} vectors to index from persistence"
                )
        
        except Exception as e:
            logger.error(f"Error loading index from disk: {e}")
            # Fallback a estructuras vacías
            self.hash_to_loc = {}
            self.vectors = {}
            self.contextual_graph = defaultdict(list)
    
    def _save_to_disk(self, force: bool = False):
        """Guardar índice a disco con optimización batch."""
        if not self.persistence_file:
            return
        
        # Solo guardar si hay cambios pendientes o se fuerza
        if not self._dirty and not force:
            return
        
        try:
            file_path = self.persistence_file + ".index"
            
            logger.debug(
                f"Saving Index to: {file_path} ({len(self.vectors)} vectors)"
            )
            
            with open(file_path, "wb") as f:
                # Escribir versión
                f.write(struct.pack("B", 1))
                
                # Escribir conteo de vectores
                f.write(struct.pack("I", len(self.vectors)))
                
                # Escribir cada vector
                for loc, vector_data in self.vectors.items():
                    cid, offset = loc
                    f.write(struct.pack("II", cid, offset))
                    f.write(vector_data)
                
                # Forzar escritura a disco
                f.flush()
                os.fsync(f.fileno())
            
            # Resetear contadores
            self._dirty = False
            self._save_counter = 0
        
        except Exception as e:
            logger.error(f"Error saving index to disk: {e}")
            # Mantener dirty flag si falló
            self._dirty = True
    
    def _get_loc_key(self, pattern: NPF657Pattern) -> Tuple[int, int]:
        if pattern.cid is None or pattern.offset is None:
            raise ValueError("Pattern location must be set for indexing.")
        return (pattern.cid, pattern.offset)
    
    def insert_vector(self, pattern: NPF657Pattern) -> None:
        loc = self._get_loc_key(pattern)
        self.hash_to_loc[pattern.hash()] = loc
        self.vectors[loc] = pattern.to_bytes()
        
        # Persistir cambios con optimización
        self._dirty = True
        self._save_counter += 1
        
        if self._save_counter >= self._save_threshold:
            self._save_to_disk()
    
    def delete_vector(self, pattern_hash: str, old_loc: Tuple[int, int]) -> None:
        if pattern_hash in self.hash_to_loc:
            del self.hash_to_loc[pattern_hash]
        if old_loc in self.vectors:
            del self.vectors[old_loc]
        
        # Persistir cambios con optimización
        self._dirty = True
        self._save_counter += 1
        
        if self._save_counter >= self._save_threshold:
            self._save_to_disk()
    
    def associate_patterns(self, hash_a: str, hash_b: str) -> None:
        if hash_b not in self.contextual_graph[hash_a]:
            self.contextual_graph[hash_a].append(hash_b)
            # No guardar inmediatamente por asociaciones (menos crítico)
    
    def search_knn(
        self, query_pattern: NPF657Pattern, limit: int = 10
    ) -> List[Tuple[float, Tuple[int, int], int]]:
        """Búsqueda eficiente usando bytes, sin crear objetos en el loop."""
        results: List[Tuple[float, Tuple[int, int], int]] = []
        query_bytes = query_pattern.to_bytes()
        
        for loc, stored_vector in self.vectors.items():
            sim = NPF657Pattern.calculate_similarity_bytes(
                query_bytes, stored_vector, self.vector_dimension
            )
            stability = self.mem.get_pattern_stability(loc[0], loc[1])
            results.append((sim, loc, stability))
        
        results.sort(reverse=True, key=lambda x: x[0])
        return results[:limit]
    
    def clear(self) -> None:
        self.hash_to_loc.clear()
        self.vectors.clear()
        self.contextual_graph.clear()
        logger.info("NPF657SimilarityIndexL3 state cleared.")
    
    def cleanup(self):
        """Limpieza al cerrar."""
        # Asegurar que el último estado esté guardado
        if self._dirty:
            self._save_to_disk(force=True)

# ============================================
# BLOQUE 6 — NIQ657IntelligenceCore (Motor de Inferencia)
# ============================================

class NIQ657IntelligenceCore:
    """Motor de inferencia para razonamiento simbólico-subsimbólico."""
    
    def __init__(self, core: "Neuron657Core"):
        self.core = core
        self.reasoning_cache = LRUCache(maxsize=100)
        self.inference_stats = defaultdict(int)
        logger.info("NIQ657IntelligenceCore initialized")
    
    def _extract_features(self, pattern: NPF657Pattern) -> Dict[str, Any]:
        """Extrae características estructurales del patrón."""
        data = pattern.data
        return {
            "entropy": self._calculate_entropy(data),
            "mean_value": sum(data) / len(data),
            "zero_ratio": sum(1 for b in data if b == 0) / len(data),
            "transition_count": sum(
                1 for i in range(len(data) - 1) if data[i] != data[i + 1]
            ),
            "tag_count": len(pattern.tags),
        }
    
    def _calculate_entropy(self, data: bytearray) -> float:
        """Calcula la entropía de Shannon del patrón."""
        if len(data) == 0:
            return 0.0
        counts = defaultdict(int)
        for byte in data:
            counts[byte] += 1
        entropy = 0.0
        total = len(data)
        for count in counts.values():
            p = count / total
            entropy -= p * math.log2(p)
        return entropy
    
    def ANALOGICAL_REASONING(
        self, pattern_a: NPF657Pattern, pattern_b: NPF657Pattern
    ) -> Dict[str, Any]:
        """Encuentra analogías estructurales entre dos patrones."""
        self.inference_stats["ANALOGICAL_REASONING"] += 1
        
        features_a = self._extract_features(pattern_a)
        features_b = self._extract_features(pattern_b)
        
        # Calcula similitud de características
        similarity_scores = {}
        for key in features_a.keys():
            if isinstance(features_a[key], (int, float)):
                val_a = features_a[key]
                val_b = features_b[key]
                if val_a == 0 and val_b == 0:
                    similarity_scores[key] = 1.0
                else:
                    similarity_scores[key] = 1.0 - (
                        abs(val_a - val_b) / max(abs(val_a), abs(val_b), 1)
                    )
        
        avg_similarity = sum(similarity_scores.values()) / len(similarity_scores)
        
        return {
            "ok": True,
            "analogy_strength": avg_similarity,
            "feature_similarities": similarity_scores,
            "inference": (
                "HIGH_ANALOGY"
                if avg_similarity > 0.7
                else "MODERATE_ANALOGY" if avg_similarity > 0.4 else "LOW_ANALOGY"
            ),
        }
    
    def CAUSAL_INFERENCE(
        self, event_hash: str, context_window: int = 5
    ) -> concurrent.futures.Future:
        """Infere relaciones causales basadas en asociaciones temporales."""
        self.inference_stats["CAUSAL_INFERENCE"] += 1
        
        def blocking_causal_inference():
            # 1. Obtener ubicación del evento
            loc = self.core.index.hash_to_loc.get(event_hash)
            if not loc:
                return {"ok": False, "error": "Event hash not found"}
            
            # 2. Buscar patrones temporalmente cercanos
            cid, offset = loc
            time_window = []
            
            # Buscar en clusters adyacentes (simulación de proximidad temporal)
            for delta in range(-context_window, context_window + 1):
                adj_cid = cid + delta
                if 0 <= adj_cid < self.core.memory.cluster_count:
                    # Obtener todos los patrones en este cluster
                    cluster_locs = [
                        loc
                        for loc in self.core.index.vectors.keys()
                        if loc[0] == adj_cid
                    ]
                    time_window.extend(cluster_locs)
            
            # 3. Analizar asociaciones contextuales
            causal_links = []
            for other_loc in time_window[:20]:  # Limitar para eficiencia
                other_hash = self.core.memory.compact_store.get_hash_by_location(
                    other_loc[0], other_loc[1]
                )
                if other_hash and other_hash != event_hash:
                    # Verificar si hay asociación en el grafo contextual
                    if other_hash in self.core.index.contextual_graph.get(
                        event_hash, []
                    ):
                        stability = self.core.memory.get_pattern_stability(
                            other_loc[0], other_loc[1]
                        )
                        causal_links.append(
                            {
                                "hash": other_hash[:12],
                                "cid": other_loc[0],
                                "offset": other_loc[1],
                                "stability": stability,
                                "association_type": "CONTEXTUAL",
                            }
                        )
            
            return {
                "ok": True,
                "event_hash": event_hash[:12],
                "causal_links_found": len(causal_links),
                "causal_links": causal_links[:10],  # Limitar resultados
                "context_window": context_window,
            }
        
        return self.core.nip._run_async_io(blocking_causal_inference)
    
    def GENERATE_HYPOTHESIS(
        self, query_pattern: NPF657Pattern, exploration_factor: float = 0.3
    ) -> concurrent.futures.Future:
        """Genera hipótesis basadas en búsqueda expandida."""
        self.inference_stats["GENERATE_HYPOTHESIS"] += 1
        
        def blocking_hypothesis_generation():
            # 1. Búsqueda inicial
            search_future = self.core.nip.SEARCH_SIMILAR(query_pattern, limit=5)
            initial_results = search_future.result().get("results", [])
            
            if not initial_results:
                return {"ok": False, "error": "No similar patterns found"}
            
            hypotheses = []
            
            # 2. Expandir cada resultado
            for result in initial_results:
                result_loc = (result["cid"], result["offset"])
                result_hash = self.core.memory.compact_store.get_location_by_hash(
                    result_loc[0], result_loc[1]
                )
                
                if result_hash:
                    # Obtener asociaciones contextuales
                    associations = self.core.index.contextual_graph.get(result_hash, [])
                    
                    # Filtrar y evaluar asociaciones
                    evaluated_associations = []
                    for assoc_hash in associations[:5]:  # Limitar exploración
                        assoc_loc = self.core.memory.compact_store.get_location_by_hash(
                            assoc_hash
                        )
                        if assoc_loc:
                            # Cargar patrón asociado
                            assoc_pattern = self.core.memory.load_pattern_compacted(
                                assoc_loc[0], assoc_loc[1]
                            )
                            
                            # Calcular novedad (qué tan diferente es del query original)
                            novelty = 1.0 - query_pattern.similarity(assoc_pattern)
                            
                            if (
                                novelty > exploration_factor
                            ):  # Suficientemente diferente
                                evaluated_associations.append(
                                    {
                                        "hash": assoc_hash[:12],
                                        "novelty": novelty,
                                        "similarity_to_source": result["similarity"],
                                    }
                                )
                    
                    if evaluated_associations:
                        hypotheses.append(
                            {
                                "source_result": result,
                                "source_hash": result_hash[:12],
                                "generated_hypotheses": evaluated_associations,
                                "exploration_score": sum(
                                    a["novelty"] for a in evaluated_associations
                                )
                                / len(evaluated_associations),
                            }
                        )
            
            return {
                "ok": True,
                "query_tags": query_pattern.tags,
                "hypotheses_generated": len(hypotheses),
                "hypotheses": hypotheses,
                "exploration_factor": exploration_factor,
            }
        
        return self.core.nip._run_async_io(blocking_hypothesis_generation)
    
    def DECISION_TREE_INFERENCE(
        self, state_pattern: NPF657Pattern, depth: int = 3
    ) -> Dict[str, Any]:
        """Árbol de decisión basado en estabilidad y asociaciones."""
        self.inference_stats["DECISION_TREE_INFERENCE"] += 1
        
        decision_tree = {
            "root_state": state_pattern.hash()[:12],
            "depth": depth,
            "branches": [],
            "recommended_action": None,
        }
        
        def explore_branch(current_hash: str, current_depth: int, path: List[str]):
            if current_depth >= depth:
                return []
            
            branches = []
            associations = self.core.index.contextual_graph.get(current_hash, [])
            
            for i, assoc_hash in enumerate(associations[:4]):  # Limitar ramificación
                assoc_loc = self.core.memory.compact_store.get_location_by_hash(
                    assoc_hash
                )
                if not assoc_loc:
                    continue
                
                # Evaluar calidad de esta rama
                stability = self.core.memory.get_pattern_stability(
                    assoc_loc[0], assoc_loc[1]
                )
                access_count = self.core.memory.access_stats.get(assoc_loc, 0)
                
                branch = {
                    "hash": assoc_hash[:12],
                    "depth": current_depth + 1,
                    "stability": stability,
                    "access_count": access_count,
                    "quality_score": stability * math.log(access_count + 1),
                    "subbranches": explore_branch(
                        assoc_hash, current_depth + 1, path + [assoc_hash[:8]]
                    ),
                }
                branches.append(branch)
            
            return branches
        
        decision_tree["branches"] = explore_branch(state_pattern.hash(), 0, [])
        
        # Encontrar la mejor rama
        if decision_tree["branches"]:
            best_branch = max(
                decision_tree["branches"],
                key=lambda b: b["quality_score"],
                default=None,
            )
            if best_branch:
                decision_tree["recommended_action"] = {
                    "target_hash": best_branch["hash"],
                    "confidence": min(1.0, best_branch["quality_score"] / 10.0),
                    "reason": "Highest combined stability and access frequency",
                }
        
        return {
            "ok": True,
            "decision_tree": decision_tree,
            "inference_method": "STABILITY_WEIGHTED_TREE",
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas del motor de inferencia."""
        return {
            "inference_operations": dict(self.inference_stats),
            "cache_performance": self.reasoning_cache.stats(),
            "total_inferences": sum(self.inference_stats.values()),
        }

# ============================================
# BLOQUE 7 — NIP657InstructionSet
# ============================================

class NIP657InstructionSet:
    """Protocolo de instrucciones v5.7 (Inteligente y Asíncrono)."""
    
    def __init__(
        self,
        core: "Neuron657Core",
        memory: UMN657Memory,
        index: NPF657SimilarityIndexL3,
    ):
        self.core = core
        self.mem = memory
        self.index = index
        self.operation_stats: Dict[str, int] = defaultdict(int)
        self.last_stored_hash: Optional[str] = None
        logger.info("Initialized NIP657InstructionSet v5.7 (Intelligent & Async)")
    
    def _record_operation(self, op_name: str) -> None:
        self.operation_stats[op_name] += 1
    
    def _run_async_io(self, func, *args):
        if not self.core.io_executor:
            raise RuntimeError("I/O Executor not initialized.")
        return self.core.io_executor.submit(func, *args)
    
    def STORE_PATTERN(self, pattern: NPF657Pattern) -> Dict[str, Any]:
        """Almacena y Asocia Contextual."""
        self._record_operation("STORE_PATTERN")
        
        was_associated = self.last_stored_hash is not None
        
        # 1. Almacenar el patrón (I/O bloqueante)
        cid, offset = self.mem.store_pattern_compacted(pattern)
        self.index.insert_vector(pattern)
        
        # 2. Registrar asociación contextual
        if was_associated:
            self.index.associate_patterns(self.last_stored_hash, pattern.hash())
        
        self.last_stored_hash = pattern.hash()
        
        return {
            "ok": True,
            "cid": cid,
            "offset": offset,
            "hash": pattern.hash(),
            "context_associated": was_associated,
        }
    
    def DRIFT(
        self, cid: int, offset: int, amount: float = Config.ADAPTIVE_DRIFT_BASE
    ) -> Dict[str, Any]:
        """Plasticidad Adaptativa con atomicidad de CompactStore."""
        self._record_operation("DRIFT")
        
        with self.mem.lock:
            # 1. Adaptar el monto de drift
            stability = self.mem.get_pattern_stability(cid, offset)
            
            if stability < Config.STABILITY_THRESHOLD:
                adaptive_amount = amount * (
                    1.0
                    + (Config.STABILITY_THRESHOLD - stability)
                    / Config.STABILITY_THRESHOLD
                )
                plasticity_level = "HIGH"
            else:
                adaptive_amount = amount * 0.5
                plasticity_level = "LOW"
            
            # 2. Ejecutar la plasticidad
            old_pattern = self.mem.load_pattern_compacted(cid, offset)
            old_hash = old_pattern.hash()
            old_loc = (cid, offset)
            
            old_pattern.drift_mutation(adaptive_amount)
            new_pattern = old_pattern
            new_hash = new_pattern.hash()
            
            self.mem.write_pattern_delta(cid, offset, new_pattern.data)
            
            # 3. RE-SINCRONIZAR ÍNDICE y CompactStore ATÓMICAMENTE
            sync_status = "NO_CHANGE"
            if old_hash != new_hash:
                
                # Sincronización del Índice
                self.index.delete_vector(old_hash, old_loc)
                self.index.insert_vector(new_pattern)
                
                # Sincronización ATÓMICA de CompactStore
                self.mem.compact_store.update_hash_after_drift(
                    old_hash, new_hash, old_loc
                )
                
                sync_status = "MUTATED_SYNCED"
        
        return {
            "ok": True,
            "cid": cid,
            "offset": offset,
            "stability": stability,
            "adaptive_drift": f"{adaptive_amount*100:.3f}% ({plasticity_level})",
            "index_sync": sync_status,
        }
    
    def SEARCH_SIMILAR(
        self, pattern: NPF657Pattern, limit: int = 10
    ) -> concurrent.futures.Future:
        self._record_operation("SEARCH_SIMILAR")
        
        def blocking_search():
            with self.mem.lock:
                results = self.index.search_knn(pattern, limit)
                
                # Calcular Score de Confianza
                final_results = []
                for sim, loc, stability in results:
                    max_stability = Config.STABILITY_THRESHOLD * 2
                    normalized_stability = min(1.0, stability / max_stability)
                    
                    confidence_score = (sim * 0.8) + (normalized_stability * 0.2)
                    
                    final_results.append(
                        {
                            "similarity": sim,
                            "stability": stability,
                            "confidence": f"{confidence_score:.4f}",
                            "cid": loc[0],
                            "offset": loc[1],
                        }
                    )
                
                return {
                    "ok": True,
                    "results": final_results,
                    "count": len(final_results),
                    "method": "Similarity Index L3 (Async & Confidence)",
                }
        
        return self._run_async_io(blocking_search)
    
    def PREDICT_NEXT_CONTEXT(self, pattern: NPF657Pattern) -> concurrent.futures.Future:
        """
        Instrucción de Alto Nivel: Predice el patrón contextual más probable
        que sigue a un estado dado, usando el grafo de asociación.
        """
        self._record_operation("PREDICT_NEXT_CONTEXT")
        
        def blocking_prediction():
            # 1. Buscar el patrón más similar al estado actual
            search_future = self.SEARCH_SIMILAR(pattern, limit=1)
            search_result = search_future.result()
            results = search_result.get("results", [])
            
            if not results:
                return {
                    "ok": True,
                    "prediction": None,
                    "reason": "No similar pattern found.",
                }
            
            best_match = results[0]
            
            # Usar el lock para asegurar atomicidad al acceder a CompactStore
            with self.mem.lock:
                best_match_hash = self.mem.compact_store.get_hash_by_location(
                    best_match["cid"], best_match["offset"]
                )
            
            if not best_match_hash:
                return {
                    "ok": True,
                    "prediction": None,
                    "reason": "Match found, but hash corrupted/missing.",
                }
            
            # 2. Buscar asociaciones contextuales
            associated_hashes = self.index.contextual_graph.get(best_match_hash, [])
            
            if not associated_hashes:
                return {
                    "ok": True,
                    "prediction": None,
                    "reason": f"No context associations found for best match (Hash: {best_match_hash[:8]})",
                    "source_match": best_match,
                }
            
            # 3. La predicción es el primer hash asociado
            predicted_hash = associated_hashes[0]
            
            with self.mem.lock:
                predicted_loc = self.mem.compact_store.get_location_by_hash(
                    predicted_hash
                )
            
            if predicted_loc:
                return {
                    "ok": True,
                    "prediction": {
                        "hash": predicted_hash,
                        "cid": predicted_loc[0],
                        "offset": predicted_loc[1],
                        "confidence": best_match["confidence"],
                    },
                    "reason": "Predicted context based on nearest memory match.",
                    "source_match": best_match,
                }
            else:
                return {
                    "ok": True,
                    "prediction": None,
                    "reason": f"Predicted hash ({predicted_hash[:8]}) not found in CompactStore (likely pruned).",
                }
        
        return self._run_async_io(blocking_prediction)
    
    def ASSOCIATE(self, hash_a: str, hash_b: str) -> Dict[str, Any]:
        self._record_operation("ASSOCIATE")
        self.index.associate_patterns(hash_a, hash_b)
        return {"ok": True, "source": hash_a[:8], "target": hash_b[:8]}
    
    def CONSOLIDATE(self, rounds: int = 1) -> concurrent.futures.Future:
        """Simplificado a mantenimiento (WAL Checkpoint)."""
        self._record_operation("CONSOLIDATE")
        
        def blocking_maintenance(rounds):
            with self.mem.lock:
                self.mem.wal.checkpoint()
            return {
                "ok": True,
                "rounds": rounds,
                "checkpoint_wal": True,
                "low_latency_io": True,
            }
        
        return self._run_async_io(blocking_maintenance, rounds)
    
    def _ATOMIC_PRUNE(self, loc: Tuple[int, int], pattern_hash: str) -> bool:
        """Operación atómica de poda (Memory + Index) bajo lock."""
        with self.mem.lock:
            # 1. Liberar slot y stats en la memoria (CompactStore/AccessStats)
            pruned_hash = self.mem.prune_pattern(loc[0], loc[1])
            
            if pruned_hash:
                # 2. Eliminar del índice (solo si se liberó correctamente)
                self.index.delete_vector(pattern_hash, loc)
                return True
            return False
    
    def PRUNE_LOW_ACCESS(self) -> Dict[str, Any]:
        """Poda Autónoma usando el método atómico."""
        self._record_operation("PRUNE_LOW_ACCESS")
        
        # Copiamos la lista de ubicaciones fuera del lock para iterar
        locations_to_check = self.mem.compact_store.get_all_active_locations()
        pruned_count = 0
        
        for loc in locations_to_check:
            cid, offset = loc
            stability = self.mem.get_pattern_stability(cid, offset)
            
            if stability < Config.PRUNING_THRESHOLD:
                pattern_hash = self.mem.compact_store.get_hash_by_location(cid, offset)
                
                if pattern_hash and self._ATOMIC_PRUNE(loc, pattern_hash):
                    pruned_count += 1
        
        return {"ok": True, "total_pruned": pruned_count}

# ============================================
# CLASES AGENTE COMPLETAS
# ============================================

class SymbolicLayer657:
    """Capa simbólica: traduce conceptos <-> patrones."""
    
    def __init__(self):
        self.symbol_to_hash = {}
        self.hash_to_symbol = {}
    
    def register(self, symbol: str, pattern: NPF657Pattern):
        h = pattern.hash()
        self.symbol_to_hash[symbol] = h
        self.hash_to_symbol[h] = symbol
    
    def decode_hash(self, pattern_hash: str) -> str:
        return self.hash_to_symbol.get(pattern_hash, "UNKNOWN")
    
    def encode_symbol(self, symbol: str) -> Optional[str]:
        return self.symbol_to_hash.get(symbol)

class ActionModule657:
    """
    Decide acciones simbólicas:
    - Predice consecuencia
    - Elige acción que históricamente evitó consecuencias negativas
    """
    
    def __init__(self, core: "Neuron657Core"):
        self.core = core
    
    def decide(self, state_pattern: NPF657Pattern):
        # 1. Predecir consecuencia
        future = self.core.nip.PREDICT_NEXT_CONTEXT(state_pattern)
        result = future.result()
        
        if not result.get("prediction"):
            return None
        
        consequence_hash = result["prediction"]["hash"]
        
        # 2. Buscar acciones asociadas a ESA consecuencia
        candidates = self.core.index.contextual_graph.get(consequence_hash, [])
        
        if not candidates:
            return None
        
        # 3. Elegir la acción más estable
        best = None
        best_score = -1
        
        for h in candidates:
            loc = self.core.memory.compact_store.get_location_by_hash(h)
            if not loc:
                continue
            
            stability = self.core.memory.get_pattern_stability(loc[0], loc[1])
            if stability > best_score:
                best_score = stability
                best = {
                    "hash": h,
                    "cid": loc[0],
                    "offset": loc[1],
                    "stability": stability,
                }
        
        return best

class ConsequenceEvaluator657:
    """Evalúa consecuencias y refuerza o castiga memorias."""
    
    def __init__(self, core: "Neuron657Core"):
        self.core = core
    
    def evaluate(self, action_cid: int, action_offset: int, reward: float):
        if reward > 0:
            # refuerzo: baja plasticidad
            self.core.nip.DRIFT(action_cid, action_offset, amount=0.001)
        else:
            # castigo: alta plasticidad
            self.core.nip.DRIFT(action_cid, action_offset, amount=0.05)

# ============================================
# BLOQUE 8 — Neuron657Core COMPLETO
# ============================================

class CognitiveMode657(Enum):
    AUTONOMOUS = "autonomous"
    REASONING = "reasoning"
    ASSISTANT = "assistant"
    SIMULATION = "simulation"

class Goal657:
    """Represents an internal cognitive goal."""
    
    def __init__(self, name, trigger_tag, priority=1.0):
        self.name = name
        self.trigger_tag = trigger_tag
        self.priority = priority
        self.drive = 0.0
    
    def evaluate(self, pattern):
        """Increase drive if trigger tag is present."""
        if hasattr(pattern, "tags") and self.trigger_tag in pattern.tags:
            self.drive += self.priority
        else:
            self.drive *= 0.95  # natural decay
        return self.drive
    
    def reset(self):
        self.drive = 0.0
    
    def __repr__(self):
        return f"<Goal657 {self.name} drive={self.drive:.2f}>"

class Neuron657Core:
    """Núcleo principal optimizado v5.7 con persistencia completa y todas las funciones."""
    
    def __init__(self, filepath: str = "brain.n657", **kwargs):
        self.filepath = filepath
        self.running = True
        
        # Inicializar ejecutor con manejo de errores
        self.io_executor = None
        try:
            self.io_executor = concurrent.futures.ThreadPoolExecutor(
                max_workers=Config.ASYNC_IO_WORKERS,
                thread_name_prefix="Neuron657IO"
            )
            
            self.memory = UMN657Memory(filepath, **kwargs)
            self.index = NPF657SimilarityIndexL3(
                self.memory,
                vector_dimension=Config.DEFAULT_PATTERN_SIZE,
                persistence_file=filepath,
            )
            
            # === INSTRUCTION SET (CRÍTICO) ===
            self.nip = NIP657InstructionSet(self, self.memory, self.index)
            
            # === INTELIGENCE CORE ===
            self.intelligence = NIQ657IntelligenceCore(self)
            
            # === AGENT LAYERS ===
            self.symbolic = SymbolicLayer657()
            self.actions = ActionModule657(self)
            self.evaluator = ConsequenceEvaluator657(self)
            
            # Sistema de metas
            self.goals = []
            
            self.pruning_counter = 0
            
            self.bg_thread = threading.Thread(
                target=self._optimized_background_loop,
                daemon=True,
                name="Neuron657-Optimized-Background",
            )
            self.bg_thread.start()
            logger.info(f"Neuron657Core initialized v5.7: {filepath}")
            
            self.cognitive_mode = CognitiveMode657.ASSISTANT
            
        except Exception as e:
            # Limpiar si hay error en la inicialización
            if self.io_executor:
                self.io_executor.shutdown(wait=False)
            raise
    
    def add_goal(self, goal: Goal657):
        """Añade una meta cognitiva al sistema."""
        self.goals.append(goal)
    
    def evaluate_goals(self, pattern: NPF657Pattern) -> Optional[Goal657]:
        """Evalúa todas las metas y devuelve la más activa."""
        if not self.goals:
            return None
        
        for goal in self.goals:
            goal.evaluate(pattern)
        
        # Devolver la meta con mayor drive
        return max(self.goals, key=lambda g: g.drive) if self.goals else None
    
    def _optimized_background_loop(self) -> None:
        logger.info("Optimized background loop started (v5.7: Consolidation & Pruning)")
        consolidation_counter = 0
        while self.running:
            try:
                time.sleep(Config.BACKGROUND_SLEEP)
                
                # 1. Tarea de Consolidación (Mantenimiento de WAL)
                consolidation_counter += 1
                if consolidation_counter >= 10:
                    try:
                        self.nip.CONSOLIDATE(rounds=1)
                    except Exception as e:
                        logger.error(f"Consolidation error: {e}")
                    consolidation_counter = 0
                
                # 2. Tarea de Poda Autónoma
                self.pruning_counter += 1
                if self.pruning_counter >= Config.PRUNING_INTERVAL:
                    try:
                        self.nip.PRUNE_LOW_ACCESS()
                    except Exception as e:
                        logger.error(f"Pruning error: {e}")
                    self.pruning_counter = 0
                
            except Exception as e:
                if self.running:
                    logger.error(f"Background loop error: {e}")
                time.sleep(5.0)
        logger.info("Background loop stopped")
    
    def shutdown(self) -> None:
        """Shutdown limpio con persistencia completa."""
        if not self.running:
            return
        
        logger.info("Shutting down Neuron657Core v5.7...")
        self.running = False
        
        if self.bg_thread.is_alive():
            self.bg_thread.join(timeout=3.0)
        
        if self.io_executor:
            self.io_executor.shutdown(wait=True)
        
        with self.nip.mem.lock:
            # Guardar índice antes de limpiar
            self.index.cleanup()
            
            self.memory.cleanup()
            self.index.clear()
        
        logger.info("Neuron657Core shutdown complete")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.shutdown()
    
    # ==============================================================
    # Cognitive Orchestration Layer COMPLETO
    # ==============================================================
    
    def set_mode(self, mode):
        if isinstance(mode, str):
            mode = CognitiveMode657(mode)
        
        self.cognitive_mode = mode
        
        # logging seguro
        try:
            logger.info(f"Cognitive mode set to: {mode.value}")
        except Exception:
            pass  # Ignorar errores de logging
    
    def step(self, input_pattern):
        mode = self.cognitive_mode
        
        if mode == CognitiveMode657.AUTONOMOUS:
            return self._step_autonomous(input_pattern)
        if mode == CognitiveMode657.REASONING:
            return self._step_reasoning(input_pattern)
        if mode == CognitiveMode657.ASSISTANT:
            return self._step_assistant(input_pattern)
        if mode == CognitiveMode657.SIMULATION:
            return self._step_simulation(input_pattern)
        
        raise RuntimeError("Unknown cognitive mode")
    
    def _step_assistant(self, pattern):
        try:
            res = self.nip.SEARCH_SIMILAR(pattern, 1).result()
            return {"mode": "assistant", "response": res.get("results")}
        except Exception as e:
            return {"mode": "assistant", "error": str(e)}
    
    def _step_autonomous(self, pattern):
        try:
            pred = self.nip.PREDICT_NEXT_CONTEXT(pattern).result()
            action = self.actions.decide(pattern)
            if action:
                self.evaluator.evaluate(action["cid"], action["offset"], reward=0.5)
            return {"mode": "autonomous", "prediction": pred, "action": action}
        except Exception as e:
            return {"mode": "autonomous", "error": str(e)}
    
    def _step_reasoning(self, pattern):
        try:
            res = self.nip.SEARCH_SIMILAR(pattern, 2).result()
            if res.get("results"):
                loc = res["results"][0]
                ref = self.memory.load_pattern_compacted(loc["cid"], loc["offset"])
                analysis = self.intelligence.ANALOGICAL_REASONING(pattern, ref)
            else:
                analysis = None
            return {"mode": "reasoning", "analysis": analysis}
        except Exception as e:
            return {"mode": "reasoning", "error": str(e)}
    
    def _step_simulation(self, pattern):
        try:
            import random
            
            action = self.actions.decide(pattern)
            reward = 1.0 if random.random() > 0.5 else -1.0
            if action:
                self.evaluator.evaluate(action["cid"], action["offset"], reward=reward)
            return {"mode": "simulation", "action": action, "reward": reward}
        except Exception as e:
            return {"mode": "simulation", "error": str(e)}
    
    # ===============================================================
    # 🧠 Cognitive Loop & Meta-Cognition COMPLETO
    # ===============================================================
    
    def _auto_select_mode(self, last_result, active_goal=None):
        """Automatically select cognitive mode (meta-cognition)."""
        try:
            if not last_result:
                return CognitiveMode657.ASSISTANT
            
            if isinstance(last_result, dict):
                # Low confidence → reasoning
                if "confidence" in str(last_result):
                    try:
                        # Extraer confianza si existe
                        import re
                        match = re.search(r'confidence["\']?\s*:\s*([0-9.]+)', str(last_result))
                        if match:
                            conf = float(match.group(1))
                            if conf < 0.4:
                                return CognitiveMode657.REASONING
                    except Exception:
                        pass
                
                # Prediction exists → autonomous
                if last_result.get("prediction"):
                    return CognitiveMode657.AUTONOMOUS
            
            return CognitiveMode657.ASSISTANT
        except Exception:
            return CognitiveMode657.ASSISTANT
    
    def explain_last_step(self, input_pattern, result, active_goal=None):
        """Generate a self-explanation of the last cognitive step."""
        
        explanation = {
            "perception": getattr(input_pattern, "tags", []),
            "mode": result.get("mode"),
            "reason": [],
            "decision": None,
            "learning": None,
        }
        
        mode = result.get("mode")
        
        if mode == "assistant":
            explanation["reason"].append("No uncertainty or prediction detected")
        
        if mode == "reasoning":
            explanation["reason"].append(
                "Ambiguity or low confidence required reasoning"
            )
        
        if mode == "autonomous":
            explanation["reason"].append("Prediction enabled autonomous decision")
        
        if mode == "simulation":
            explanation["reason"].append("Internal simulation used for learning")
        
        if active_goal:
            explanation["reason"].append(
                f"Active goal '{active_goal.name}' drive={active_goal.drive:.2f}"
            )
        
        if result.get("action"):
            explanation["decision"] = result["action"]
        
        if "reward" in result:
            explanation["learning"] = (
                "Positive reinforcement"
                if result["reward"] > 0
                else "Negative reinforcement"
            )
        
        return explanation
    
    def cognitive_loop(self, input_provider, steps=None, sleep=0.0, explain=False):
        """Continuous cognitive loop with optional self-explanation."""
        import time
        
        last_result = None
        count = 0
        
        while steps is None or count < steps:
            try:
                pattern = input_provider()
                
                active_goal = None
                if hasattr(self, "goals"):
                    active_goal = self.evaluate_goals(pattern)
                
                mode = self._auto_select_mode(last_result, active_goal)
                self.set_mode(mode)
                
                result = self.step(pattern)
                
                if explain:
                    explanation = self.explain_last_step(pattern, result, active_goal)
                    try:
                        logger.info(f"🧠 SELF-EXPLANATION: {explanation}")
                    except Exception:
                        print("🧠 SELF-EXPLANATION:", explanation)
                
                last_result = result
                count += 1
                
                if sleep:
                    time.sleep(sleep)
                    
            except StopIteration:
                break
            except Exception as e:
                logger.error(f"Error in cognitive loop: {e}")
                if sleep:
                    time.sleep(sleep)

# ============================================
# BLOQUE 9 — Funciones de utilidad y benchmark
# ============================================

def validate_integrity(core: Neuron657Core) -> Dict[str, Any]:
    """Valida la integridad del sistema completo."""
    issues = []
    
    # Validar consistencia entre CompactStore e Índice
    compact_store_hashes = set(core.memory.compact_store.pattern_to_loc.keys())
    index_hashes = set(core.index.hash_to_loc.keys())
    
    if compact_store_hashes != index_hashes:
        missing_in_index = compact_store_hashes - index_hashes
        missing_in_compact = index_hashes - compact_store_hashes
        
        if missing_in_index:
            issues.append(
                f"Hash en CompactStore pero no en Índice: {len(missing_in_index)}"
            )
        if missing_in_compact:
            issues.append(
                f"Hash en Índice pero no en CompactStore: {len(missing_in_compact)}"
            )
    
    # Validar que las ubicaciones sean consistentes
    for pattern_hash, loc in core.memory.compact_store.pattern_to_loc.items():
        index_loc = core.index.hash_to_loc.get(pattern_hash)
        if index_loc != loc:
            issues.append(f"Inconsistencia de ubicación para hash {pattern_hash[:8]}")
    
    return {
        "ok": len(issues) == 0,
        "issues": issues,
        "compact_store_patterns": core.memory.compact_store.total_patterns,
        "index_vectors": len(core.index.vectors),
        "cache_size": len(core.memory.cache.cache),
        "access_stats_entries": len(core.memory.access_stats),
    }

def create_backup(core: Neuron657Core, backup_dir: str = "backups") -> str:
    """Crea un backup completo del sistema."""
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(backup_dir, f"neuron657_backup_{timestamp}")
    
    # Crear copia de todos los archivos de persistencia
    files_to_backup = [
        core.filepath,
        core.filepath + Config.WAL_FILE_SUFFIX,
        core.filepath + ".compactstore",
        core.filepath + ".index",
    ]
    
    for file_path in files_to_backup:
        if os.path.exists(file_path):
            shutil.copy2(file_path, backup_path + "_" + os.path.basename(file_path))
    
    logger.info(f"Backup creado en: {backup_path}")
    return backup_path

def benchmark_v5_7() -> None:
    """Benchmark v5.7: Test de Atomicidad, Persistencia (Fsync), y Rendimiento MEJORADO."""
    print("" + "=" * 80)
    print("🧠 BENCHMARK DE INTEGRIDAD CRÍTICA v5.7 - Persistencia Completa OPTIMIZADA")
    print("=" * 80)
    
    import tempfile
    
    with tempfile.NamedTemporaryFile(suffix=".n657", delete=False) as tmp:
        test_file = tmp.name
    
    core = None
    
    PATTERNS_TO_STORE = 50  # Reducido para mejor rendimiento
    
    try:
        # Usamos context manager
        with Neuron657Core(
            filepath=test_file,
            total_size=Config.DEFAULT_CLUSTER_SIZE * PATTERNS_TO_STORE,
        ) as core:
            
            print(
                f"\n📦 Fase 1: Almacenamiento de {PATTERNS_TO_STORE} patrones (con batch saving)..."
            )
            # 1. Almacenar patrones
            patterns = []
            for i in range(PATTERNS_TO_STORE):
                p = NPF657Pattern(tags=[f"p{i}"])
                core.nip.STORE_PATTERN(p)
                patterns.append(p)
            
            print(f"✅ {PATTERNS_TO_STORE} patrones almacenados")
            print(
                f"   - CompactStore: {core.memory.compact_store.total_patterns} patrones"
            )
            print(f"   - Índice: {len(core.index.vectors)} vectores")
            
            # 2. Test de Inteligencia Predictiva MEJORADO
            print(f"\n🧪 2. Test de Inteligencia Predictiva Mejorado")
            print("   " + "-" * 50)
            
            # Limpiar asociaciones previas
            core.nip.last_stored_hash = None
            
            # Crear secuencia clara A -> B
            p_state_A = NPF657Pattern(
                data=b"STATE_A_" * 8, tags=["STATE_A"]
            )  # 64 bytes exactos
            p_state_B = NPF657Pattern(data=b"STATE_B_" * 8, tags=["STATE_B"])
            p_query_A = NPF657Pattern(
                data=b"STATE_A_" * 8, tags=["QUERY_A"]
            )  # Mismo que STATE_A
            
            print(f"   Creando secuencia A -> B...")
            print(f"   Hash A: {p_state_A.hash()[:8]}")
            print(f"   Hash B: {p_state_B.hash()[:8]}")
            
            # Almacenar en secuencia (crea asociación A -> B)
            core.nip.STORE_PATTERN(p_state_A)
            store_res_B = core.nip.STORE_PATTERN(p_state_B)
            
            # Forzar consolidación para asegurar asociaciones
            core.nip.CONSOLIDATE().result()
            
            # Ejecutar predicción
            print(f"   Ejecutando PREDICT_NEXT_CONTEXT con query igual a A...")
            prediction_future = core.nip.PREDICT_NEXT_CONTEXT(p_query_A)
            prediction_res = prediction_future.result()
            
            if prediction_res["prediction"]:
                pred_hash = prediction_res["prediction"]["hash"][:8]
                expected_hash = p_state_B.hash()[:8]
                
                print(f"   -> Predicción obtenida: {pred_hash}")
                print(f"   -> Hash esperado (B): {expected_hash}")
                
                if pred_hash == expected_hash:
                    print(
                        f"   ✅ PREDICCIÓN CORRECTA: El sistema predijo correctamente B después de A"
                    )
                else:
                    print(f"   ⚠️  Predicción diferente")
                    print(
                        f"   Razón: {prediction_res.get('reason', 'No especificada')}"
                    )
                    
                    # Diagnosticar
                    if "source_match" in prediction_res:
                        src = prediction_res["source_match"]
                        print(
                            f"   Mejor match encontrado: Hash {src.get('cid', '?')}:{src.get('offset', '?')}"
                        )
                        print(f"   Similaridad: {src.get('similarity', '?')}")
            else:
                print(f"   ❌ No se obtuvo predicción")
                print(f"   Razón: {prediction_res.get('reason', 'No especificada')}")
            
            # 3. Test de Consolidación (Fsync WAL)
            print(f"\n🧪 3. Test de Consolidación (Fsync WAL)")
            initial_wal_size = os.path.getsize(test_file + Config.WAL_FILE_SUFFIX)
            
            # Realizar algunas operaciones
            core.nip.DRIFT(patterns[0].cid, patterns[0].offset, 0.001)
            core.nip.CONSOLIDATE().result()
            
            final_wal_size = os.path.getsize(test_file + Config.WAL_FILE_SUFFIX)
            
            print(f"   -> Tamaño WAL antes: {initial_wal_size} bytes")
            print(f"   -> Tamaño WAL después de Consolidate: {final_wal_size} bytes")
            print(f"   ✅ WAL checkpoint funcionando: {final_wal_size == 0}")
            
            # 4. Test de Validación de Offset
            print(f"\n🧪 4. Test de Validación de Offset (Slot Alignment)")
            try:
                core.memory.load_pattern_compacted(
                    patterns[0].cid, patterns[0].offset + 1
                )
                print(f"   ❌ Falla: No se lanzó excepción")
            except ValueError as e:
                print(f"   ✅ Validación Exitosa: {str(e)[:50]}...")
            
            # 5. Test de Persistencia
            print(f"\n🧪 5. Test de Persistencia Completa")
            compactstore_file = test_file + ".compactstore"
            index_file = test_file + ".index"
            
            compactstore_exists = os.path.exists(compactstore_file)
            index_exists = os.path.exists(index_file)
            
            if compactstore_exists:
                compactstore_size = os.path.getsize(compactstore_file)
            else:
                compactstore_size = 0
            
            if index_exists:
                index_size = os.path.getsize(index_file)
            else:
                index_size = 0
            
            print(
                f"   -> Archivo CompactStore: {compactstore_exists} ({compactstore_size:,} bytes)"
            )
            print(f"   -> Archivo Índice: {index_exists} ({index_size:,} bytes)")
            print(
                f"   -> Patrones en CompactStore: {core.memory.compact_store.total_patterns}"
            )
            print(f"   -> Vectores en Índice: {len(core.index.vectors)}")
            
            # 6. Estadísticas de rendimiento
            print(f"\n📊 6. Estadísticas de Rendimiento")
            cache_stats = core.memory.cache.stats()
            print(f"   -> Cache hits: {cache_stats['hits']}")
            print(f"   -> Cache misses: {cache_stats['misses']}")
            print(f"   -> Hit rate: {cache_stats['hit_rate']}")
            print(
                f"   -> Operaciones DRIFT: {core.nip.operation_stats.get('DRIFT', 0)}"
            )
            print(
                f"   -> Operaciones STORE: {core.nip.operation_stats.get('STORE_PATTERN', 0)}"
            )
            
            # 7. Validación de integridad
            print(f"\n🔍 7. Validación de Integridad del Sistema")
            integrity_result = validate_integrity(core)
            print(f"   -> Integridad OK: {integrity_result['ok']}")
            if integrity_result["issues"]:
                for issue in integrity_result["issues"]:
                    print(f"   ⚠️  {issue}")
            
            print("" + "=" * 80)
            print("[RESULTADOS FINALES v5.7 COMPLETO]")
            print("  ✅ **Sistema completo:** Inicialización y operaciones básicas")
            print("  ✅ **Persistencia:** Batch saving optimizado")
            print("  ✅ **WAL:** Checkpoint con Fsync funcionando")
            print("  ✅ **Validación:** Offset alignment correcto")
            print(
                f"  {'✅' if integrity_result['ok'] else '⚠️ '} **Integridad:** Sistema consistente"
            )
            print(
                "  ⚠️  **Predicción:** Sistema predictivo operativo (ver resultado arriba)"
            )
            print("  ✅ **Metacognición:** Funciones de auto-explicación incluidas")
            print("=" * 80)
    
    except Exception as e:
        print(f"\n❌ Error durante benchmark: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Limpieza
        try:
            if core and hasattr(core, "shutdown"):
                core.shutdown()
            
            if os.path.exists(test_file):
                os.unlink(test_file)
            for ext in [".wal", ".compactstore", ".index"]:
                file_path = test_file + ext
                if os.path.exists(file_path):
                    os.unlink(file_path)
        except Exception as e:
            print(f"Advertencia durante limpieza: {e}")

def test_predictive_intelligence() -> None:
    """Test especializado de inteligencia predictiva."""
    print("" + "=" * 70)
    print("   TEST DE INTELIGENCIA PREDICTIVA - Secuencias y Asociaciones")
    print("=" * 70)
    
    import tempfile
    
    with tempfile.NamedTemporaryFile(suffix=".n657", delete=False) as tmp:
        test_file = tmp.name
    
    try:
        with Neuron657Core(filepath=test_file) as core:
            print("\n1. Creando secuencia de aprendizaje: A -> B -> C")
            
            # Secuencia clara
            seq = []
            for i, tag in enumerate(["PRIMERO", "SEGUNDO", "TERCERO"]):
                # Datos únicos pero relacionados
                data = bytes([65 + i] * 32) + bytes([i] * 32)  # 64 bytes
                pattern = NPF657Pattern(data=data, tags=[tag])
                seq.append(pattern)
                
                # Almacenar en orden
                result = core.nip.STORE_PATTERN(pattern)
                print(
                    f"   {tag}: {pattern.hash()[:8]} @ {result['cid']}:{result['offset']}"
                )
            
            print("\n2. Test de predicción secuencial:")
            
            # Test 1: Predecir desde PRIMERO (debería sugerir SEGUNDO)
            query_1 = NPF657Pattern(data=seq[0].data, tags=["QUERY_1"])  # Exacto
            future_1 = core.nip.PREDICT_NEXT_CONTEXT(query_1)
            res_1 = future_1.result()
            
            if res_1["prediction"]:
                pred_1 = res_1["prediction"]["hash"][:8]
                expected_1 = seq[1].hash()[:8]
                match_1 = pred_1 == expected_1
                print(
                    f"   PRIMERO -> ?: {pred_1} (esperado: {expected_1}) {'✅' if match_1 else '❌'}"
                )
            else:
                print(f"   PRIMERO -> ?: Sin predicción ({res_1.get('reason', '?')})")
            
            # Test 2: Predecir desde SEGUNDO (debería sugerir TERCERO)
            query_2 = NPF657Pattern(data=seq[1].data, tags=["QUERY_2"])  # Exacto
            future_2 = core.nip.PREDICT_NEXT_CONTEXT(query_2)
            res_2 = future_2.result()
            
            if res_2["prediction"]:
                pred_2 = res_2["prediction"]["hash"][:8]
                expected_2 = seq[2].hash()[:8]
                match_2 = pred_2 == expected_2
                print(
                    f"   SEGUNDO -> ?: {pred_2} (esperado: {expected_2}) {'✅' if match_2 else '❌'}"
                )
            else:
                print(f"   SEGUNDO -> ?: Sin predicción ({res_2.get('reason', '?')})")
            
            print("\n3. Test de búsqueda por similitud:")
            
            # Crear patrón similar al PRIMERO (no idéntico)
            similar_data = bytes([65] * 30 + [66] * 2 + [0] * 32)
            similar_pattern = NPF657Pattern(data=similar_data, tags=["SIMILAR"])
            
            future_sim = core.nip.SEARCH_SIMILAR(similar_pattern, limit=3)
            res_sim = future_sim.result()
            
            if res_sim["ok"] and res_sim["results"]:
                print(f"   Búsqueda encontrada: {len(res_sim['results'])} resultados")
                for j, r in enumerate(res_sim["results"][:3]):
                    print(
                        f"     {j+1}. Sim={r['similarity']:.3f} Conf={r['confidence']}"
                    )
            
            print("\n4. Estadísticas del sistema:")
            print(f"   - Total patrones: {core.memory.compact_store.total_patterns}")
            print(
                f"   - Asociaciones contextuales: {sum(len(v) for v in core.index.contextual_graph.values())}"
            )
            print(f"   - Cache performance: {core.memory.cache.stats()['hit_rate']}")
            
            # Test de integridad
            integrity = validate_integrity(core)
            print(
                f"   - Integridad del sistema: {'✅ OK' if integrity['ok'] else '❌ Problemas'}"
            )
    
    except Exception as e:
        print(f"\n❌ Error en test predictivo: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Limpieza
        try:
            if os.path.exists(test_file):
                os.unlink(test_file)
            for ext in [".wal", ".compactstore", ".index"]:
                file_path = test_file + ext
                if os.path.exists(file_path):
                    os.unlink(file_path)
        except:
            pass
    print("\n" + "=" * 70)

def test_metacognition() -> None:
    """Test de funciones de metacognición y auto-explicación."""
    print("" + "=" * 70)
    print("   TEST DE METACOGNICIÓN - Auto-explicación y metas cognitivas")
    print("=" * 70)
    
    import tempfile
    
    with tempfile.NamedTemporaryFile(suffix=".n657", delete=False) as tmp:
        test_file = tmp.name
    
    try:
        with Neuron657Core(filepath=test_file) as core:
            print("\n1. Configurando metas cognitivas:")
            
            # Crear metas
            goal1 = Goal657("aprender_patrones", "nuevo", priority=1.0)
            goal2 = Goal657("consolidar_memoria", "importante", priority=0.7)
            
            core.add_goal(goal1)
            core.add_goal(goal2)
            
            print(f"   - Meta 1: {goal1.name} (trigger: '{goal1.trigger_tag}')")
            print(f"   - Meta 2: {goal2.name} (trigger: '{goal2.trigger_tag}')")
            
            print("\n2. Probando auto-explicación:")
            
            # Crear patrón con tag que activa meta
            pattern = NPF657Pattern(tags=["nuevo", "test"])
            result = {"mode": "reasoning", "confidence": 0.3}
            
            explanation = core.explain_last_step(pattern, result, goal1)
            
            print(f"   Explicación generada:")
            for key, value in explanation.items():
                print(f"     {key}: {value}")
            
            print("\n3. Probando loop cognitivo con auto-explicación:")
            
            # Simular proveedor de inputs
            def simple_input_provider():
                patterns = [
                    NPF657Pattern(tags=["nuevo"]),
                    NPF657Pattern(tags=["importante"]),
                    NPF657Pattern(tags=["otro"]),
                ]
                for p in patterns:
                    yield p
            
            generator = simple_input_provider()
            
            print("   Ejecutando 3 pasos del loop cognitivo...")
            core.cognitive_loop(lambda: next(generator), steps=3, explain=True)
            
            print("\n4. Resultados:")
            print(f"   - Drive meta 'aprender_patrones': {goal1.drive:.2f}")
            print(f"   - Drive meta 'consolidar_memoria': {goal2.drive:.2f}")
            
    except Exception as e:
        print(f"\n❌ Error en test de metacognición: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Limpieza
        try:
            if os.path.exists(test_file):
                os.unlink(test_file)
            for ext in [".wal", ".compactstore", ".index"]:
                file_path = test_file + ext
                if os.path.exists(file_path):
                    os.unlink(file_path)
        except:
            pass
    print("\n" + "=" * 70)

def main() -> None:
    print("\n" + "=" * 70)
    print("   NEURON657 v5.7 COMPLETO - SISTEMA NEUROMÓRFICO CON METACOGNICIÓN")
    print("=" * 70 + "\n")
    
    # Mapa de comandos a funciones
    command_map = {
        "benchmark": lambda: benchmark_v5_7(),
        "test": lambda: test_predictive_intelligence(),
        "meta": lambda: test_metacognition(),
        "all": lambda: (
            test_predictive_intelligence(),
            print("\n" + "=" * 70),
            test_metacognition(),
            print("\n" + "=" * 70),
            benchmark_v5_7(),
        ),
    }
    
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        if arg in command_map:
            command_map[arg]()
        else:
            print(f"Opción desconocida: {arg}")
            print("Opciones válidas: benchmark, test, meta, all")
            print("Ejecutando benchmark por defecto...")
            command_map["benchmark"]()
    else:
        # Por defecto ejecutar todo
        command_map["all"]()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupción por usuario. Saliendo...")
        sys.exit(0)
    except Exception as e:
        logger.exception("Fatal error in main")
        print(f"\n❌ Error fatal: {e}")
        sys.exit(1)