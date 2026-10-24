# Guia do Comprador

App web para conferir a proposta da concessionária na hora: taxa real de juros, valores escondidos na parcela, preço comparado com a FIPE, IPVA do seu estado e custo mensal do carro (parcela, seguro, combustível, IPVA e manutenção). Funciona para 0 km e seminovos.

**Nenhum dado do usuário sai do aparelho.** As propostas salvas ficam só no navegador de quem usa.

## Como funciona

| Dado | Origem | Atualização |
|---|---|---|
| FIPE | API pública Parallelum, consultada ao vivo pelo navegador | na hora |
| CEP → cidade/UF | ViaCEP | na hora |
| IPVA | `data/ipva.json` (alíquota geral por UF) | manual, 1x por ano |
| Taxa média de juros | Banco Central, série SGS 20749 → `data/taxas.json` | robô semanal |
| Gasolina/etanol | ANP, levantamento semanal → `data/combustivel.json` | robô semanal |
| Consumo e revisões | `data/modelos.json` (Inmetro e tabelas das marcas) | manual |

## Publicação (custo zero)

1. **Settings → Pages → Build and deployment → Source: GitHub Actions.**
2. O workflow **Publicar site** roda a cada push e coloca o site em `https://<usuario>.github.io/guia-do-comprador/`.
3. O workflow **Atualizar dados** roda toda segunda. Para rodar agora: **Actions → Atualizar dados → Run workflow**.

Se a ANP ou o Banco Central estiverem fora do ar, o robô mantém o último valor e o app continua funcionando.

## Rodar localmente

```bash
python3 -m http.server 8000   # abra http://localhost:8000
```

> Estimativas para ajudar na negociação. Não substituem o CET oficial do contrato.
