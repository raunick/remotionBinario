# Integração de SVG no remotionBinario (via Yarn/Node.js)

Sim, é totalmente possível integrar SVGs ao seu fluxo de trabalho usando ferramentas do ecossistema Node.js (Yarn).

Temos duas abordagens principais para trazer "qualquer desenho" para o framework:

## 1. Abordagem VETORIAL (SVG -> YAML)
Nesta abordagem, lemos o código do SVG e tentamos recriar as formas usando os elementos nativos do `remotionBinario` (`rect`, `circle`, `line`).

*   **Vantagens**: A animação permanece leve e totalmente editável via código.
*   **Limitações**: O `remotionBinario` atualmente suporta poucos primitivos. Desenhos complexos com curvas Bezier, caminhos arbitrários (`<path>`) ou gradientes seriam muito difíceis de converter fielmente sem atualizar a engine Python primeiro.

## 2. Abordagem RASTER/SPRITE (SVG -> PNG Sprite) 🌟 *Recomendada*
Nesta abordagem, usamos o Yarn para criar um script que "tira uma foto" do SVG em alta qualidade, converte para preto e branco (1-bit) e gera um arquivo pronto para ser usado como `sprite`.

*   **Vantagens**: Aceita **qualquer desenho** (logotipos, ilustrações complexas, ícones). O resultado visual é garantido.
*   **Recursos Confirmados**:
    *   **Dithering (Floyd-Steinberg)**: Para simular sombras sem "chapar" a imagem.
    *   **Auto-Crop**: Remove espaços vazios automaticamente (`sharp.trim()`).
    *   **Pixel Perfect**: Escalonamento com `nearest` para manter a nitidez 8-bit.
    *   **Exportação C (.h)**: Gera `static const uint8_t` direto para Flash (economiza RAM do ESP32).
    *   **Sprite Sheets**: Junta múltiplos frames de animação em uma única imagem.
    *   **Inversão de Cor**: Flag `--invert` para telas OLED.

*   **Implementação Sugerida**:
    1.  Criar pasta `tools/svg_importer` com Node.js + `sharp`.
    2.  Script CLI robusto com flags: `--dither`, `--invert`, `--c-header`.
    3.  Exemplo de uso:
        ```bash
        yarn convert icon.svg --width 32 --dither --c-header
        ```

## Próximos Passos
Se você aprovar, posso configurar o ambiente **Yarn** agora mesmo na pasta `tools/` e criar o script de conversão para a Abordagem 2.
