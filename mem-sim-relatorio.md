
# Relatório do Simulador de Memória Virtual

**Nome:** Maria Eduarda Xavier Messias  


**RA:** 183611  

---


## 1) Visão geral 

Implementei um simulador de memória virtual com:

* **TLB** totalmente associativa usando **LRU**.

  > A **TLB** é sempre **LRU** (exigência do enunciado).
* **Memória física (RAM)** com duas políticas de substituição: **LRU** e **SecondChance (Clock)**.

  > Comecei com **LRU** (mais fácil de validar) e depois adicionei **SecondChance** para entender, na prática, como o ponteiro do **Clock** muda a página vítima.
* **Tradução de endereços** centralizada: `VA → (VPN, OFFSET)`.
  Mantive o invariante: se `page_table[p] = f`, então `frames[f] = p`.
* **Contadores**: `tlb_hits`, `tlb_misses`, `page_faults`.
* **Testes**: casos simples para comparar políticas; dois conjuntos com **500 acessos**; e cenários com **500 hits** e **500 misses** na TLB.

---

## 2) Testes detalhados

**O que eu testo**

* Se o fluxo **TLB → Page Table → Page Fault → (LRU/Clock)** funciona.
* Se os contadores batem: `tlb_hits`, `tlb_misses`, `page_faults`.

**Como gero as entradas (traces)**

* **Simples (LRU vs SC)**: `lru_sc_simple_trace.in` com `0, 4, 0, 8, 4` (`page=4` ⇒ VPN `0,1,0,2,1`).
* **set1** (500 acessos, localidade): repito páginas `0..31` → `set1_trace.in`.
* **set2** (500 acessos, pouca localidade): `p = (p + 17) % 1024` → `set2_trace.in`.
* **TLB 500/500** (1000 acessos): `0..499` e repete → `tlb_500_500_trace.in`.

**Como defino as saídas esperadas (sem viés)**

* Para esses 6 casos, deixei os *expected* manuais, derivados por raciocínio (páginas únicas, capacidade da TLB e de frames).
  **Não** gerei os *expected* com o próprio simulador.

**Como comparo com o obtido**

* `python main.py` imprime “(esperado)” e “(obtido)” no mesmo formato e mostra `comparacao: IGUAIS/DIFERENTES`.
* Ao final, sai um resumo: total de testes, quantos passaram e quantas falhas.

**Regras rápidas (sanidade)**

* `tlb_hits + tlb_misses = número de acessos`.
* Com muitos frames: `page_faults = páginas únicas do trace`.
* Com poucos frames: `page_faults ≥ páginas únicas do trace`.

---

## 3) Como foi feito

* **Interface**: alinhei o construtor ao `main.py` com `replacement_policy` e acrescentei `va_bits` (padrão **32**).
  Usei 32 bits por ser comum no material da disciplina e suficiente para os testes.
* **Validações**: tipos corretos, valores `> 0`, **potências de 2** e `page_size ≤ 2**va_bits`.
  Usei `math.log2(page_size)` para obter `offset_bits`.
* **Por que `OrderedDict` na TLB (LRU)**: mantém a ordem de uso.
  “Tiro e recoloco” a chave para marcar como mais recente; `popitem(last=False)` remove o mais antigo — **LRU** claro e confiável.
* **Helpers implementados (papel de cada um)**

  * `tlb_busca`, `tlb_insere`, `tlb_remover`: operar a **TLB LRU**.
  * `va_para_pagina_offset`: converter **VA** em **(VPN, OFFSET)**.
  * `pegar_frame_livre`: devolver um quadro livre rapidamente.
  * `lru_escolhe_pagina`, `sc_escolhe_pagina`: decidir a vítima na **RAM**.
  * `marca_uso_memoria`: atualizar a política a cada acesso (em LRU move; em SC marca `ref=1`).
  * `carregar_pagina`, `remover_da_ram`, `obter_frame_para_pagina`: instalar/retirar páginas e orquestrar substituição.
* **Fluxo de acesso**:
  **TLB → Page Table → Page Fault (se preciso) → Alocação/Substituição (LRU/Clock) → Atualizações**, contando tudo.
* **Memória física – LRU**: outro `OrderedDict` (`vpn → frame`): acesso move ao fim; expulsão tira do começo.
* **Memória física – SecondChance (Clock)**: `ref_bits[frame]` + **ponteiro** circular; em acesso marca `ref=1`. Na expulsão: se `ref=1`, zera e avança; a primeira com `ref=0` sai.
* **Saída**: mantive o formato do exemplo do enunciado, indicando **TLB = LRU** e **RAM = LRU ou SecondChance**.
* **Testes**: além do `trace.in`, criei 6 conjuntos: 2 com 500 acessos, 2 com 1000 acessos (500 hits + 500 misses na TLB) e 2 casos simples (LRU vs SC).

---

## 4) Arquitetura e estruturas

* **Configuração**: `page_size`, `num_tlb_entries`, `num_frames`, `replacement_policy` (`'LRU' | 'SecondChance'`), `va_bits`.
* **Derivados**:
  `offset_bits = log2(page_size)`, `vpn_bits = va_bits - offset_bits`, além de `ram_bytes` e `tlb_reach_bytes`.
* **Estruturas principais**

  * `tlb: OrderedDict[vpn → frame]` (fim = mais recente).
  * `page_table: dict[vpn → frame]` (apenas residentes).
  * `frames: list[frame] = vpn | None` (estado da RAM).
  * `free_frames: list[int]` (quadros livres).
  * `mem_lru: OrderedDict[vpn → frame]` (LRU na RAM).
  * `ref_bits: list[int]` e `ponteiro: int` (Clock na RAM).
* **Contadores**: `tlb_hits`, `tlb_misses`, `page_faults`.

---

## 5) Métodos principais e **auxiliares recomendados**

**Principal**

* `access_memory(virtual_address)`: executa o fluxo completo do acesso e atualiza estatísticas.

**Auxiliares (implementados)**

* `va_para_pagina_offset(va)`
* `tlb_busca(vpn)` / `tlb_insere(vpn, frame)` / `tlb_remover(vpn)`
* `pegar_frame_livre()`
* `marca_uso_memoria(pagina, frame)`
* `lru_escolhe_pagina()` / `sc_escolhe_pagina()`
* `remover_da_ram(pagina, frame)` / `carregar_pagina(pagina, frame)`
* `obter_frame_para_pagina(pagina)`

---

## 6) Políticas de substituição

**LRU**

* Ideia: sai quem foi usado há mais tempo.
* Como: `OrderedDict` (acesso move ao fim; vítima é o primeiro).

**SecondChance (Clock)**

* Ideia: dá “uma segunda chance” a páginas recém-usadas.
* Como: `ref_bits` + ponteiro circular (marca `ref=1` em acesso; na varredura, zera `1` e pula; remove a primeira com `ref=0`).

**Mini-exemplo** (`page_size=4`, `frames=2`, `tlb=2`; páginas: `0,1,0,2,1`)

* **LRU**: `Hits=1`, `Misses=4`, `Faults=4`.
* **SecondChance**: `Hits=2`, `Misses=3`, `Faults=3`.

---

## 7) Tradução de endereço (passo a passo)

**Fórmulas**

```python
offset_bits = log2(page_size)
vpn_bits    = va_bits - offset_bits
VPN         = VA >> offset_bits
OFFSET      = VA & ((1 << offset_bits) - 1)
```

**Ordem do acesso implementada**

1. **TLB**: se VPN está na TLB → **hit** (atualiza recência).
2. **Page Table**: se residente → pega frame, insere na TLB, marca uso na RAM.
3. **Page Fault**: pega frame livre **ou** escolhe vítima (LRU/SC), carrega a página, insere na TLB e marca uso.

---

## 8) Testes 

### Tabela-resumo

| ID                    | Objetivo             | Configuração                                          | Entrada                  | Esperado            | Obtido | Status | Observações                          |
| --------------------- | -------------------- | ----------------------------------------------------- | ------------------------ | ------------------- | ------ | ------ | ------------------------------------ |
| **simple LRU**        | Validar LRU mínimo   | `page=4`, `frames=2`, `tlb=2`, `LRU`, `va=8`          | `0,4,0,8,4`              | `H=1 M=4 F=4`       | Igual  | ✅      | Evicções por recência                |
| **simple SC**         | Comparar com Clock   | `page=4`, `frames=2`, `tlb=2`, `SC`, `va=8`           | `0,4,0,8,4`              | `H=2 M=3 F=3`       | Igual  | ✅      | Clock “perdoa” uma página            |
| **TLB 500/500 (LRU)** | 500 hits/500 misses  | `page=4096`, `frames=1024`, `tlb=512`, `LRU`, `va=32` | `0..499` e repete (1000) | `H=500 M=500 F=500` | Igual  | ✅      | 1ª metade carrega; 2ª bate na TLB    |
| **TLB 500/500 (SC)**  | Mesmo cenário com SC | `page=4096`, `frames=1024`, `tlb=512`, `SC`, `va=32`  | `0..499` e repete        | `H=500 M=500 F=500` | Igual  | ✅      | RAM folgada; política não muda fault |
| **set1 LRU 500**      | Localidade           | `page=4096`, `frames=64`, `tlb=16`, `LRU`, `va=32`    | `tests/set1_trace.in`    | `H=0 M=500 F=32`    | Igual  | ✅      | RAM retém, TLB não                   |
| **set2 LRU 500**      | Baixa localidade     | `page=4096`, `frames=64`, `tlb=16`, `LRU`, `va=32`    | `tests/set2_trace.in`    | `H=0 M=500 F=500`   | Igual  | ✅      | Sem reuso ⇒ muitos faults            |

### Detalhe dos cenários

* **Simples (LRU vs SC)**
  `tests/lru_sc_simple_trace.in`: endereços `0,4,0,8,4` (com `page=4` ⇒ VPN `0,1,0,2,1`).
  Resultados salvos em `tests/saida_lru_simple.in` e `tests/saida_sc_simple.in`.

* **Conjuntos de 500 acessos**

  * **set1 (localidade)**: repito páginas `0..31` (`VA = p * page_size`).
  * **set2 (baixa localidade)**: sequência pseudo-dispersa `p = (p + 17) % 1024`.
    Traços em `tests/set1_trace.in` e `tests/set2_trace.in`; saídas em `tests/saida_set1.in` e `tests/saida_set2.in`.

* **TLB 500/500 (1000 acessos)**
  `tests/tlb_500_500_trace.in`: primeiro `0..499` (carrega), depois repete (bate na TLB).
  Com `tlb=512` e `frames=1024`, a 2ª metade não gera novos faults.
  Salvei `tests/saida_tlb_500_500_lru.in` e `tests/saida_tlb_500_500_sc.in`.

---
