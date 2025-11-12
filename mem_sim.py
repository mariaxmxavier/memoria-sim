import collections
import math

# usei a lib math para verificar se e potencia de 2 e calcular bits
# Foi trocado o rep_policy por replacement_policy para nao precisar alterar a main
# add va_bits; para simplificar deixei o default como 32
# TLB: cache de traducoes VA->frame; pequena e rapida, evita ir na pagina/RAM
# LRU: politica que privilegia uso mais recente (recency); a TLB usa LRU


class MemorySimulator:
    def __init__(self, page_size, num_tlb_entries, num_frames, replacement_policy, va_bits=32):
        """
        Inicializa o simulador de memoria virtual.

        Parametros
        - page_size (int): Tamanho da pagina em bytes.
        - num_tlb_entries (int): Numero de entradas da TLB (associativa total / fully-associative).
        - num_frames (int): Numero de quadros (frames) na memoria fisica.
        - replacement_policy (str): Politica de substituicao de paginas na memoria ('LRU' ou 'SecondChance').
        - va_bits (int, opcional): Numero de bits do endereco virtual do processo.
        """

        # [Adicao] Armazenando parametros basicos do simulador
        self.page_size = page_size
        self.num_tlb_entries = num_tlb_entries
        self.num_frames = num_frames
        self.replacement_policy = replacement_policy
        self.va_bits = va_bits

        # [Validacao] Politica de substituicao permitida
        if self.replacement_policy not in ['LRU', 'SecondChance']:
            raise ValueError("Politica de substituicao invalida. Use 'LRU' ou 'SecondChance'.")

        # [Validacao] Tipos e dominio basico dos parametros
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

        # [Validacao] Potencias de 2 conforme a especificacao
        if not self._is_power_of_two(self.page_size):
            raise ValueError("page_size deve ser potencia de 2")
        if not self._is_power_of_two(self.num_tlb_entries):
            raise ValueError("num_tlb_entries deve ser potencia de 2")
        if not self._is_power_of_two(self.num_frames):
            raise ValueError("num_frames deve ser potencia de 2")

        # [Validacao] Compatibilidade entre page_size e va_bits
        max_endereco_em_bytes = 1 << self.va_bits  # 2**va_bits
        if self.page_size > max_endereco_em_bytes:
            raise ValueError("page_size nao pode ser maior que o espaco de enderecos (2**va_bits)")

        # [Derivados] Bits de deslocamento e de VPN
        self.offset_bits = int(math.log2(self.page_size))  # ex.: 4096 -> 12
        self.vpn_bits = self.va_bits - self.offset_bits
        if self.vpn_bits <= 0:
            raise ValueError(
                "va_bits deve ser maior que log2(page_size): precisa sobrar pelo menos 1 bit para a VPN."
            )

        # [Derivados] Metricas uteis (nao impressas)
        self.ram_bytes = self.num_frames * self.page_size
        self.tlb_reach_bytes = self.num_tlb_entries * self.page_size

        # [Alteracao] TLB como OrderedDict para suportar LRU
        self.tlb = collections.OrderedDict()
        self.page_table = {}
        self.frames = [None] * self.num_frames

        # [Adicao] Contadores de estatisticas
        self.tlb_hits = 0
        self.tlb_misses = 0
        self.page_faults = 0

        # [Adicao] Estruturas de reposicao de paginas (memoria)
        # validacao para os testes
        self.free_frames = list(range(self.num_frames))
        self.mem_lru = collections.OrderedDict()  # usado quando politica = LRU
        self.ref_bits = [0] * self.num_frames     # usado quando politica = SecondChance
        self.ponteiro = 0                        # ponteiro circular para SecondChance

    # [Adicao] Utilitario para verificar potencia de 2
    # validacao para os testes
    @staticmethod
    def _is_power_of_two(n: int) -> bool:
        """Retorna True se n e potencia de 2 (n > 0)."""
        return isinstance(n, int) and n > 0 and (n & (n - 1)) == 0

    # [Adicao] Conversao de VA em (pagina, offset)
    # validacao para os testes
    def va_para_pagina_offset(self, virtual_address: int):
        """Retorna (page_number, offset) do endereco virtual informado."""
        if not isinstance(virtual_address, int) or virtual_address < 0:
            raise TypeError("virtual_address deve ser int nao-negativo")
        page_number = virtual_address >> self.offset_bits
        offset = virtual_address & ((1 << self.offset_bits) - 1)
        return page_number, offset

    # [Adicao] Busca na TLB (LRU)
    # validacao para os testes
    def tlb_busca(self, page_number: int):
        """Retorna frame_number se a pagina esta na TLB; atualiza LRU/contadores."""
        if page_number in self.tlb:
            frame_number = self.tlb.pop(page_number)
            self.tlb[page_number] = frame_number  # move para o fim (mais recente)
            self.tlb_hits += 1
            return frame_number
        else:
            self.tlb_misses += 1
            return None

    # [Adicao] Insercao/atualizacao na TLB (LRU)
    # validacao para os testes
    def tlb_insere(self, page_number: int, frame_number: int):
        """Insere/atualiza; se cheia, remove a entrada menos recente (LRU)."""
        # se ja existe, atualizo a posicao (recency)
        if page_number in self.tlb:
            self.tlb.pop(page_number)
            self.tlb[page_number] = frame_number
            return
        # se cheia, remove o mais antigo (LRU)
        if len(self.tlb) >= self.num_tlb_entries:
            self.tlb.popitem(last=False)
        self.tlb[page_number] = frame_number

    # [Adicao] Remocao de pagina da TLB
    # validacao para os testes
    def tlb_remover(self, page_number: int):
        """Remove da TLB se presente (nao mexe em contadores)."""
        if page_number in self.tlb:
            self.tlb.pop(page_number)

    # [Adicao] Pego um frame livre, se existir
    # validacao para os testes
    def pegar_frame_livre(self):
        """Retorna um indice de frame livre ou None se nao houver."""
        if self.free_frames:
            return self.free_frames.pop(0)
        return None

    # [Adicao] Marco uso da pagina na memoria
    # validacao para os testes
    def marca_uso_memoria(self, pagina: int, frame: int):
        """Atualiza estruturas conforme a politica (LRU: recency; SC: ref_bit=1)."""
        if self.replacement_policy == 'LRU':
            if pagina in self.mem_lru:
                self.mem_lru.pop(pagina)
            self.mem_lru[pagina] = frame  # move para o fim (mais recente)
        else:  # SecondChance
            self.ref_bits[frame] = 1

    # [Adicao] Escolho vitima pela politica LRU na RAM
    # validacao para os testes
    def lru_escolhe_pagina(self):
        """Retorna (pagina, frame) menos recente na memoria (LRU)."""
        if self.mem_lru:
            pagina, frame = self.mem_lru.popitem(last=False)
            return pagina, frame
        # fallback: procura primeiro frame ocupado
        for frame, pagina in enumerate(self.frames):
            if pagina is not None:
                return pagina, frame
        raise RuntimeError('Sem pagina para evictar (inconsistencia)')

    # [Adicao] Escolho vitima pela politica SecondChance (clock)
    # validacao para os testes
    def sc_escolhe_pagina(self):
        """Retorna (pagina, frame) usando algoritmo do relogio (SecondChance)."""
        n = self.num_frames
        loops = 0
        while True:
            frame = self.ponteiro
            pagina = self.frames[frame]
            if pagina is None:
                # frame livre, nao e vitima; avanca
                self.ponteiro = (self.ponteiro + 1) % n
            elif self.ref_bits[frame] == 1:
                # da segunda chance e zera o bit
                self.ref_bits[frame] = 0
                self.ponteiro = (self.ponteiro + 1) % n
            else:
                # bit 0: escolhe como vitima
                self.ponteiro = (self.ponteiro + 1) % n
                return pagina, frame
            loops += 1
            if loops > 2 * n:
                # seguranca: se nao achou, escolhe primeiro ocupado
                for f, p in enumerate(self.frames):
                    if p is not None:
                        self.ponteiro = (f + 1) % n
                        return p, f

    # [Adicao] Removo uma pagina da RAM e atualizo estruturas
    # validacao para os testes
    def remover_da_ram(self, pagina: int, frame: int):
        """Remove pagina do frame, TLB e estruturas auxiliares; libera o frame."""
        # tira da tabela de paginas
        if pagina in self.page_table:
            self.page_table.pop(pagina, None)
        # tira da TLB
        self.tlb_remover(pagina)
        # limpa estruturas por politica
        if self.replacement_policy == 'LRU':
            if pagina in self.mem_lru:
                self.mem_lru.pop(pagina, None)
        else:  # SecondChance
            self.ref_bits[frame] = 0
        # libera o frame
        self.frames[frame] = None
        if frame not in self.free_frames:
            self.free_frames.append(frame)

    # [Adicao] Carrego pagina em um frame (atualiza RAM e estruturas)
    # validacao para os testes
    def carregar_pagina(self, pagina: int, frame: int):
        """Coloca pagina no frame, atualiza tabela e estruturas de politica."""
        self.frames[frame] = pagina
        self.page_table[pagina] = frame
        self.marca_uso_memoria(pagina, frame)

    # [Adicao] Obtenco um frame para a pagina (livre ou apos reposicao)
    # validacao para os testes
    def obter_frame_para_pagina(self, pagina: int):
        """Retorna frame: usa livre se houver; senao evicta de acordo com a politica."""
        frame = self.pegar_frame_livre()
        if frame is not None:
            return frame
        # precisa evictar
        if self.replacement_policy == 'LRU':
            vit_pagina, vit_frame = self.lru_escolhe_pagina()
        else:
            vit_pagina, vit_frame = self.sc_escolhe_pagina()
        self.remover_da_ram(vit_pagina, vit_frame)
        # apos remover, pegar um livre
        frame = self.pegar_frame_livre()
        if frame is None:
            # deve existir um livre agora; fallback usa o vit_frame
            frame = vit_frame
        return frame
    # [Adicao] Acesso a memoria virtual
    # validacao para os testes
    def access_memory(self, virtual_address):
        """
        Simula o acesso a um endereco virtual.
        Deve atualizar os contadores e aplicar a politica de substituicao se necessario.
        """
        # traduz VA para pagina/offset
        pagina, _ = self.va_para_pagina_offset(virtual_address)

        # tenta TLB (LRU)
        frame = self.tlb_busca(pagina)
        if frame is not None:
            # hit de TLB: marcar uso na memoria (LRU/SC)
            self.marca_uso_memoria(pagina, frame)
            return

        # miss de TLB: verifica se pagina ja esta na RAM
        frame = self.page_table.get(pagina)
        if frame is not None:
            # pagina em RAM: inserir na TLB e marcar uso
            self.tlb_insere(pagina, frame)
            self.marca_uso_memoria(pagina, frame)
            return

        # page fault: precisa trazer pagina para a RAM
        self.page_faults += 1
        frame = self.obter_frame_para_pagina(pagina)
        self.carregar_pagina(pagina, frame)
        self.tlb_insere(pagina, frame)
        return

    # [Adicao] Impressao das estatisticas
    # validacao para os testes
    def print_statistics(self):
        print("=" * 60)
        print("SIMULADOR DE MEMORIA - Estatisticas de Acesso")
        print("=" * 60)
        # [Alteracao] Rotulo de politica mais claro (TLB sempre LRU)
        # validacao para os testes
        if self.replacement_policy == 'LRU':
            policy_label = 'LRU (TLB e Memoria)'
        else:
            policy_label = 'LRU (TLB) e SecondChance (Memoria)'
        print(f"Politica de Substituicao:   {policy_label}")
        print(f"Tamanho da Pagina:          {self.page_size} bytes")
        print(f"Entradas na TLB:            {self.num_tlb_entries}")
        print(f"Numero de Frames:           {self.num_frames}")
        print("-" * 60)
        print(f"TLB Hits:                   {self.tlb_hits:,}")
        print(f"TLB Misses:                 {self.tlb_misses:,}")
        print(f"Page Faults:                {self.page_faults:,}")
        print("=" * 60)

    # [Adicao] Impressao das tabelas (TLB, page table e frames)
    # validacao para os testes
    def print_tables(self):
        # TLB
        print("TLB (ordem: mais antigo -> mais recente)")
        if not self.tlb:
            print("  [vazia]")
        else:
            idx = 0
            for pg, fr in self.tlb.items():
                print(f"  {idx:02d}: pagina {pg} -> frame {fr}")
                idx += 1
        # Page Table (somente residentes)
        print("Page Table (paginas residentes)")
        if not self.page_table:
            print("  [vazia]")
        else:
            # ordenar por frame para facilitar leitura
            for pg, fr in sorted(self.page_table.items(), key=lambda x: x[1]):
                print(f"  pagina {pg} -> frame {fr}")
        # Frames
        print("Frames (frame: pagina)")
        for i, pg in enumerate(self.frames):
            if pg is None:
                print(f"  {i:02d}: -")
            else:
                print(f"  {i:02d}: {pg}")



