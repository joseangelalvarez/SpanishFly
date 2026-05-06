# SpanishFly Suite — Portugues

SpanishFly e uma suite modular de conteudo com IA local para criadores que querem resultado profissional sem complexidade tecnica.

![SpanishFly Hero](docs/media/hero-spanishfly.svg)

---

## O que voce precisa antes de comecar

Antes de instalar, certifique-se de ter:

- **Windows 10 ou Windows 11** (64 bits)
- **Pelo menos 16 GB de RAM** e **30 GB de espaco livre em disco**
- **GPU NVIDIA recomendada** com 8 GB de VRAM ou mais (funciona sem GPU tambem, mas muito mais lento)
- **Conexao com a internet** para instalacao e download dos modelos
- Uma **conta gratuita no Hugging Face** para baixar os modelos de IA (veja o passo 2)

---

## Passo 1 — Baixar o projeto

1. Clique no botao verde **Code** no topo desta pagina do GitHub
2. Selecione **Download ZIP**
3. Extraia a pasta ZIP em algum lugar do seu computador (ex.: Area de Trabalho ou `C:\SpanishFly`)

> Voce tambem pode clonar com Git se souber como: `git clone https://github.com/joseangelalvarez/SpanishFly.git`

---

## Passo 2 — Criar sua conta e token no Hugging Face

O SpanishFly baixa seus modelos de IA do Hugging Face. Voce precisa de uma conta gratuita e de um token de acesso.

1. Crie uma conta em [https://huggingface.co/join](https://huggingface.co/join)
2. Verifique seu email e faca login
3. Acesse [https://huggingface.co/settings/tokens](https://huggingface.co/settings/tokens)
4. Clique em **New token**, selecione o tipo **Read** e de um nome a ele (ex.: `spanishfly`)
5. Copie o token — ele comeca com `hf_...` — voce precisara dele durante a instalacao

> O token e salvo apenas no seu computador, em `Persona/data/hf_credentials.json`. Nunca o compartilhe.

---

## Passo 3 — Executar o instalador

1. Abra a pasta onde voce extraiu o SpanishFly
2. **Faca duplo clique** no arquivo **`setup_spanishfly.bat`**
3. Se o Windows perguntar se voce confia no arquivo, clique em **"Executar mesmo assim"**
4. O instalador sera aberto em uma janela preta (console) e fara tudo automaticamente:
   - Verificar os requisitos do sistema e avisar se algo estiver abaixo do minimo
   - Instalar o Python 3.10 automaticamente (voce nao precisa instalar manualmente)
   - Criar um ambiente de trabalho isolado
   - Instalar todas as dependencias
   - Perguntar se voce quer baixar os modelos de IA agora (pressione S ou Y e insira seu token do Hugging Face)
5. A primeira instalacao pode levar **entre 10 e 40 minutos** dependendo da velocidade da internet e se voce baixar os modelos

> Se o Windows bloquear o script PowerShell, execute primeiro no PowerShell: `Set-ExecutionPolicy -Scope Process Bypass`

---

## Passo 4 — Abrir o aplicativo

- Ao terminar a instalacao, o aplicativo abre automaticamente
- Para abri-lo novamente no futuro sem reinstalar, **faca duplo clique** em **`open_spanishfly.bat`**

---

## O que o SpanishFly inclui hoje

- **Persona** — Editor de personagens com IA: gere imagens de personagens a partir de uma descricao, imagem de referencia e configuracoes de estilo
- **Storyboard, Video, Voz** — Em breve

---

## Arquivos importantes em resumo

| Arquivo | Finalidade |
|---|---|
| `setup_spanishfly.bat` | Instala tudo (duplo clique) |
| `open_spanishfly.bat` | Abre o app sem reinstalar |
| `Persona/setup_persona.bat` | Instala apenas o modulo Persona |

---

## O que o instalador verifica

O instalador confere seu sistema e mostra uma tabela de resultados:

| Status | Significado |
|---|---|
| OK | Requisito atendido |
| WARN | Aviso: voce pode continuar mas o desempenho pode ser menor |
| ERROR | Requisito nao atendido: a instalacao para ate que seja corrigido |

---

## Guia do editor Persona

Uma vez dentro do aplicativo, no editor Persona:

- **Nome do personagem** (obrigatorio): identifica e salva o personagem
- **Imagem de referencia** (opcional): foto ou imagem que o modelo usara como base de estilo
- **Prompt** (obrigatorio): descricao do personagem — ingles da os melhores resultados
- **Estilo de imagem**: preset visual aplicado automaticamente
- **Prompt negativo**: o que o modelo deve evitar (pre-configurado, editavel)
- **Steps / CFG / Tamanho / Seed**: controles avancados de geracao
- **ControlNet**: ativa o controle de pose com uma imagem de referencia
- **Modo NSFW**: ativa o modelo alternativo (requer download previo)

As imagens geradas sao salvas em `Persona/outputs/personas/<nome>/`.

---

## Seguranca

- Nao publique `Persona/data/hf_credentials.json` em nenhum repositorio publico
- Os arquivos de modelos e as imagens geradas estao excluidos do historico Git por padrao
