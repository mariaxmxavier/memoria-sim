import io
from contextlib import redirect_stdout

from mem_sim import MemorySimulator

mem_simulator = MemorySimulator(page_size=4096, num_tlb_entries=16, num_frames=64, replacement_policy='LRU', va_bits=32)


arq_test = open("tests/trace.in", "r")

for addr in arq_test:
    mem_simulator.access_memory(int(addr))
mem_simulator.print_statistics()

# testes automatizados : roda traces e compara com saidas esperadas
def _run_sim(trace_path, page_size, tlb_entries, frames, policy, va_bits):
    sim = MemorySimulator(page_size, tlb_entries, frames, policy, va_bits)
    with open(trace_path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            sim.access_memory(int(line))
    # capturo somente as estatisticas no formato padrao
    buf_stats = io.StringIO()
    with redirect_stdout(buf_stats):
        sim.print_statistics()
    return buf_stats.getvalue()

tests = [
    # simples primeiro
    {
        'name': 'simple LRU',
        'trace': 'tests/lru_sc_simple_trace.in',
        'expected': 'tests/saida_lru_simple.in',
        'params': dict(page_size=4, tlb_entries=2, frames=2, policy='LRU', va_bits=8),
    },
    {
        'name': 'simple SecondChance',
        'trace': 'tests/lru_sc_simple_trace.in',
        'expected': 'tests/saida_sc_simple.in',
        'params': dict(page_size=4, tlb_entries=2, frames=2, policy='SecondChance', va_bits=8),
    },
    # novos: 500 hits e 500 misses em TLB (1000 acessos no total)
    {
        'name': 'TLB 500 hits / 500 misses (LRU)',
        'trace': 'tests/tlb_500_500_trace.in',
        'expected': 'tests/saida_tlb_500_500_lru.in',
        'params': dict(page_size=4096, tlb_entries=512, frames=1024, policy='LRU', va_bits=32),
    },
    {
        'name': 'TLB 500 hits / 500 misses (SecondChance)',
        'trace': 'tests/tlb_500_500_trace.in',
        'expected': 'tests/saida_tlb_500_500_sc.in',
        'params': dict(page_size=4096, tlb_entries=512, frames=1024, policy='SecondChance', va_bits=32),
    },
    # conjuntos maiores
    {
        'name': 'set1 LRU 500',
        'trace': 'tests/set1_trace.in',
        'expected': 'tests/saida_set1.in',
        'params': dict(page_size=4096, tlb_entries=16, frames=64, policy='LRU', va_bits=32),
    },
    {
        'name': 'set2 LRU 500',
        'trace': 'tests/set2_trace.in',
        'expected': 'tests/saida_set2.in',
        'params': dict(page_size=4096, tlb_entries=16, frames=64, policy='LRU', va_bits=32),
    },
]

print("\n=== TESTES AUTOMATIZADOS (formato padrao) ===")
for tc in tests:
    try:
        out = _run_sim(tc['trace'], **tc['params'])
        with open(tc['expected'], 'r') as fexp:
            exp = fexp.read()
        # imprime os blocos no formato padrao
        print(f"\n--- {tc['name']} (esperado) ---")
        print(exp, end='' if exp.endswith('\n') else '\n')
        print(f"--- {tc['name']} (obtido) ---")
        print(out, end='' if out.endswith('\n') else '\n')
        print('\n' * 2, end='')
    except FileNotFoundError as e:
        print(f"- {tc['name']}: SKIP ({e})")

