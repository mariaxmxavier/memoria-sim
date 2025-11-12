import collections
# usei a lib math para verificar se é potência de 2 e calcular bits
import math


# Foi trocado o rep_policy por replacement_policy para não precisar alterar a main
# add va_bits; para simplificar deixei o default como 32
class MemorySimulator:
    def __init__(self, page_size, num_tlb_entries, num_frames, replacement_policy, va_bits=32):
        """
        Inicializa o simulador de memória virtual.

        Parâmetros
        - page_size (int): Tamanho da página em bytes.
        - num_tlb_entries (int): Número de entradas da TLB (associativa total / fully-associative).
        - num_frames (int): Número de quadros (frames) na memória física.
        - replacement_policy (str): Política de substituição de páginas na memória ('LRU' ou 'SecondChance').
        - va_bits (int, opcional): Número de bits do endereço virtual do processo.
        """

        # [Adição] Armazenando parâmetros básicos do simulador
        self.page_size = page_size
        self.num_tlb_entries = num_tlb_entries
        self.num_frames = num_frames
        self.replacement_policy = replacement_policy
        self.va_bits = va_bits

        # [Validação] Política de substituição permitida
        if self.replacement_policy not in ['LRU', 'SecondChance']:
            raise ValueError("Política de substituição inválida. Use 'LRU' ou 'SecondChance'.")

        # [Validação] Tipos e domínio básico dos parâmetros
        for nome, valor in (
            ("page_size", self.page_size),
            ("num_tlb_entries", self.num_tlb_entries),
            ("num_frames", self.num_frames),
            ("va_bits", self.va_bits),
        ):
            if not isinstance(valor, int):
                raise TypeError(f"{nome} deve ser int, recebido: {type(valor).__name__}")
        if self.page_size <= 0:
            raise ValueError("page_size deve ser maior que zero")
        if self.num_tlb_entries <= 0:
            raise ValueError("num_tlb_entries deve ser maior que zero")
        if self.num_frames <= 0:
            raise ValueError("num_frames deve ser maior que zero")
        if self.va_bits <= 0:
            raise ValueError("va_bits deve ser maior que zero")

        # [Validação] Potências de 2 conforme a especificação
        if not self._is_power_of_two(self.page_size):
            raise ValueError("page_size deve ser potência de 2")
        if not self._is_power_of_two(self.num_tlb_entries):
            raise ValueError("num_tlb_entries deve ser potência de 2")
        if not self._is_power_of_two(self.num_frames):
            raise ValueError("num_frames deve ser potência de 2")

        # [Validação] Compatibilidade entre page_size e va_bits
        max_endereco_em_bytes = 1 << self.va_bits  # 2**va_bits
        if self.page_size > max_endereco_em_bytes:
            raise ValueError("page_size não pode ser maior que o espaço de endereços (2**va_bits)")

        # [Derivados] Bits de deslocamento e de VPN
        self.offset_bits = int(math.log2(self.page_size))  # ex.: 4096 -> 12
        self.vpn_bits = self.va_bits - self.offset_bits
        if self.vpn_bits <= 0:
            raise ValueError(
                "va_bits deve ser maior que log2(page_size): precisa sobrar pelo menos 1 bit para a VPN."
            )

        # [Derivados] Métricas úteis (não impressas)
        self.ram_bytes = self.num_frames * self.page_size
        self.tlb_reach_bytes = self.num_tlb_entries * self.page_size

        # [Adição] Estruturas básicas (TLB, Tabela de Páginas e Frames)
        self.tlb = []
        self.page_table = {}
        self.frames = [None] * self.num_frames

        # [Adição] Contadores de estatísticas
        self.tlb_hits = 0
        self.tlb_misses = 0
        self.page_faults = 0

    # [Adição] Utilitário para verificar potência de 2
    @staticmethod
    def _is_power_of_two(n: int) -> bool:
        """Retorna True se n é potência de 2 (n > 0)."""
        return isinstance(n, int) and n > 0 and (n & (n - 1)) == 0

    def access_memory(self, virtual_address):
        """
        Simula o acesso a um endereço virtual.
        Deve atualizar os contadores e aplicar a política de substituição se necessário.
        """
        pass

    def print_statistics(self):
        print("=" * 60)
        print("SIMULADOR DE MEMÓRIA - Estatísticas de Acesso")
        print("=" * 60)
        print(f"Política de Substituição:   {self.replacement_policy}")
        print(f"Tamanho da Página:          {self.page_size} bytes")
        print(f"Entradas na TLB:            {self.num_tlb_entries}")
        print(f"Número de Frames:           {self.num_frames}")
        print("-" * 60)
        print(f"TLB Hits:                   {self.tlb_hits:,}")
        print(f"TLB Misses:                 {self.tlb_misses:,}")
        print(f"Page Faults:                {self.page_faults:,}")
        print("=" * 60)

