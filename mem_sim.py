import collections


# Modifiquei o rep_policy para replacement_policy, para não ter que modificar a main.py
# Impletei o va_bits com valor default 32, para não ter que modificar a main.py


class MemorySimulator:
    def __init__(self, page_size, num_tlb_entries, num_frames, replacement_policy, va_bits=32):
        
        """
        Inicializa o simulador de memória virtual.

        Parâmetros
        - page_size (int): Tamanho da página em bytes.
        - num_tlb_entries (int): Número de entradas da TLB (associativa por conjunto total).
        - num_frames (int): Número de quadros (frames) na memória física.
        - replacement_policy (str): Política de substituição de páginas na memória física.
          Valores aceitos: 'LRU' ou 'SecondChance'. (A TLB será sempre LRU.)
        - va_bits (int, opcional): Quantidade de bits do endereço virtual do processo.
        """
        self.page_size = page_size
        self.num_tlb_entries = num_tlb_entries
        self.num_frames = num_frames
        self.replacement_policy = replacement_policy
        self.va_bits = va_bits

        if replacement_policy not in ['LRU', 'SecondChance']:
            raise ValueError("Política de substituição inválida. Use 'LRU' ou 'SecondChance'.")

        self.tlb = []  
        self.page_table = {} 
        self.frames = [None] * num_frames

        # contadores de estatísticas
        self.tlb_hits = 0
        self.tlb_misses = 0
        self.page_faults = 0


    def access_memory(self, virtual_address):
        """
        Simula o acesso a um endereço virtual.
        Deve atualizar os contadores e aplicar a política de substituição se necessário.
        """
        

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
