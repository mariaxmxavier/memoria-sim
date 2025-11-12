import collections
# usei a lib math para verificar se Ã© potÃªncia de 2 e calcular bits
import math


# Foi trocado o rep_policy por replacement_policy para nÃ£o precisar alterar a main
# add va_bits; para simplificar deixei o default como 32
class MemorySimulator:
    def __init__(self, page_size, num_tlb_entries, num_frames, replacement_policy, va_bits=32):
        """
        Inicializa o simulador de memÃ³ria virtual.

        ParÃ¢metros
        - page_size (int): Tamanho da pÃ¡gina em bytes.
        - num_tlb_entries (int): NÃºmero de entradas da TLB (associativa total / fully-associative).
        - num_frames (int): NÃºmero de quadros (frames) na memÃ³ria fÃ­sica.
        - replacement_policy (str): PolÃ­tica de substituiÃ§Ã£o de pÃ¡ginas na memÃ³ria ('LRU' ou 'SecondChance').
        - va_bits (int, opcional): NÃºmero de bits do endereÃ§o virtual do processo.
        """

        # [AdiÃ§Ã£o] Armazenando parÃ¢metros bÃ¡sicos do simulador
        self.page_size = page_size
        self.num_tlb_entries = num_tlb_entries
        self.num_frames = num_frames
        self.replacement_policy = replacement_policy
        self.va_bits = va_bits

        # [ValidaÃ§Ã£o] PolÃ­tica de substituiÃ§Ã£o permitida
        if self.replacement_policy not in ['LRU', 'SecondChance']:
            raise ValueError("PolÃ­tica de substituiÃ§Ã£o invÃ¡lida. Use 'LRU' ou 'SecondChance'.")

        # [ValidaÃ§Ã£o] Tipos e domÃ­nio bÃ¡sico dos parÃ¢metros
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

        # [ValidaÃ§Ã£o] PotÃªncias de 2 conforme a especificaÃ§Ã£o
        if not self._is_power_of_two(self.page_size):
            raise ValueError("page_size deve ser potÃªncia de 2")
        if not self._is_power_of_two(self.num_tlb_entries):
            raise ValueError("num_tlb_entries deve ser potÃªncia de 2")
        if not self._is_power_of_two(self.num_frames):
            raise ValueError("num_frames deve ser potÃªncia de 2")

        # [ValidaÃ§Ã£o] Compatibilidade entre page_size e va_bits
        max_endereco_em_bytes = 1 << self.va_bits  # 2**va_bits
        if self.page_size > max_endereco_em_bytes:
            raise ValueError("page_size nÃ£o pode ser maior que o espaÃ§o de endereÃ§os (2**va_bits)")

        # [Derivados] Bits de deslocamento e de VPN
        self.offset_bits = int(math.log2(self.page_size))  # ex.: 4096 -> 12
        self.vpn_bits = self.va_bits - self.offset_bits
        if self.vpn_bits <= 0:
            raise ValueError(
                "va_bits deve ser maior que log2(page_size): precisa sobrar pelo menos 1 bit para a VPN."
            )

        # [Derivados] MÃ©tricas Ãºteis (nÃ£o impressas)
        self.ram_bytes = self.num_frames * self.page_size
        self.tlb_reach_bytes = self.num_tlb_entries * self.page_size

        # [MudanÃ§a] TLB como OrderedDict para suportar LRU
        self.tlb = collections.OrderedDict()
        self.page_table = {}
        self.frames = [None] * self.num_frames

        # [AdiÃ§Ã£o] Contadores de estatÃ­sticas
        self.tlb_hits = 0
        self.tlb_misses = 0
        self.page_faults = 0

    # [O que] Verifico se um nÃºmero Ã© potÃªncia de 2
    # Uso isso nas validaÃ§Ãµes exigidas pelo enunciado
    @staticmethod
    def _is_power_of_two(n: int) -> bool:
        """Retorna True se n Ã© potÃªncia de 2 (n > 0)."""
        return isinstance(n, int) and n > 0 and (n & (n - 1)) == 0

    # [O que] Converto VA em (nÃºmero da pÃ¡gina, offset)
    # [Por quÃª] Facilita a leitura e evita repetir cÃ¡lculos de bits
    def va_para_pagina_offset(self, virtual_address: int):
        """Retorna (page_number, offset) do endereÃ§o virtual informado."""
        if not isinstance(virtual_address, int) or virtual_address < 0:
            raise TypeError("virtual_address deve ser int nÃ£o-negativo")
        page_number = virtual_address >> self.offset_bits
        offset = virtual_address & ((1 << self.offset_bits) - 1)
        return page_number, offset

    # [O que] Busco a pÃ¡gina na TLB (LRU)
    # [Por quÃª] Contabilizo hit/miss e atualizo recÃªncia para a polÃ­tica LRU
    def tlb_busca(self, page_number: int):
        """Retorna frame_number se a pÃ¡gina estÃ¡ na TLB; atualiza LRU/contadores."""
        if page_number in self.tlb:
            frame_number = self.tlb.pop(page_number)
            self.tlb[page_number] = frame_number  # move para o fim (mais recente)
            self.tlb_hits += 1
            return frame_number
        else:
            self.tlb_misses += 1
            return None

    # [O que] Insiro/atualizo a TLB respeitando LRU
    # [Por quÃª] Preciso manter a TLB coerente e dentro da capacidade
    def tlb_insere(self, page_number: int, frame_number: int):
        """Insere/atualiza; se cheia, remove a entrada menos recente (LRU)."""
        # se jÃ¡ existe, atualizo a posiÃ§Ã£o (recÃªncia)
        if page_number in self.tlb:
            self.tlb.pop(page_number)
            self.tlb[page_number] = frame_number
            return
        # se cheia, remove o mais antigo (LRU)
        if len(self.tlb) >= self.num_tlb_entries:
            self.tlb.popitem(last=False)
        self.tlb[page_number] = frame_number

    # [O que] Removo uma pÃ¡gina da TLB, se existir
    # [Por quÃª] Uso ao desalocar/evictar pÃ¡ginas da memÃ³ria fÃ­sica
    def tlb_remover(self, page_number: int):
        """Remove da TLB se presente (nÃ£o mexe em contadores)."""
        if page_number in self.tlb:
            self.tlb.pop(page_number)

    # [O que] Realizo o acesso Ã  memÃ³ria virtual
    # [Por quÃª] MÃ©todo principal: atualiza TLB/PT e contadores
    def access_memory(self, virtual_address):
        """
        Simula o acesso a um endereÃ§o virtual.
        Deve atualizar os contadores e aplicar a polÃ­tica de substituiÃ§Ã£o se necessÃ¡rio.
        """
        pass

    # [O que] Imprimo as estatÃ­sticas coletadas
    # [Por quÃª] ConferÃªncia com saÃ­da esperada e relatÃ³rio
    def print_statistics(self):
        print("=" * 60)
        print("SIMULADOR DE MEMÃ“RIA - EstatÃ­sticas de Acesso")
        print("=" * 60)
        print(f"PolÃ­tica de SubstituiÃ§Ã£o:   {self.replacement_policy}")
        print(f"Tamanho da PÃ¡gina:          {self.page_size} bytes")
        print(f"Entradas na TLB:            {self.num_tlb_entries}")
        print(f"NÃºmero de Frames:           {self.num_frames}")
        print("-" * 60)
        print(f"TLB Hits:                   {self.tlb_hits:,}")
        print(f"TLB Misses:                 {self.tlb_misses:,}")
        print(f"Page Faults:                {self.page_faults:,}")
        print("=" * 60)

