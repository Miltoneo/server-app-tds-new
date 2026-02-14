# Configuração de Ambientes - Construtora

## 📋 Visão Geral

Este diretório contém arquivos de configuração para diferentes ambientes de execução do projeto.

## 🔧 Conceitos Importantes

### 1. `DJANGO_ENV` - Variável de Ambiente do Sistema
Define o **ambiente de execução** do projeto:
- `development` → Carrega `.env.dev`
- `production` → Carrega `.env.prod`

⚠️ **IMPORTANTE**: Esta variável deve ser configurada **NO SISTEMA OPERACIONAL**, não dentro dos arquivos `.env`.

### 2. `DEBUG` - Flag do Django
Define se o Django deve **exibir erros detalhados**:
- `DEBUG=True` → Mostra stack traces completos (para troubleshooting)
- `DEBUG=False` → Mostra páginas de erro genéricas (segurança)

✅ **Definido dentro do arquivo `.env.dev` ou `.env.prod`**

---

## 🚀 Como Configurar

### **Windows (Desenvolvimento)**

#### PowerShell (Usuário atual):
```powershell
[System.Environment]::SetEnvironmentVariable('DJANGO_ENV', 'development', 'User')
```

#### PowerShell (Sistema - requer admin):
```powershell
[System.Environment]::SetEnvironmentVariable('DJANGO_ENV', 'development', 'Machine')
```

#### Verificar configuração:
```powershell
$env:DJANGO_ENV
# Deve retornar: development
```

#### Reiniciar terminal/IDE após configurar!

---

### **Linux (Produção)**

#### Temporário (sessão atual):
```bash
export DJANGO_ENV=production
```

#### Permanente (bashrc/zshrc):
```bash
echo 'export DJANGO_ENV=production' >> ~/.bashrc
source ~/.bashrc
```

#### Systemd Service:
```ini
# /etc/systemd/system/construtora.service
[Service]
Environment="DJANGO_ENV=production"
```

#### Docker Compose:
```yaml
services:
  app:
    environment:
      - DJANGO_ENV=production
```

---

## 📁 Arquivos de Ambiente

### `.env.dev` - Desenvolvimento
- `DEBUG=True` - Erros detalhados
- `EMAIL_BACKEND=console` - Emails no console
- `USE_REDIS=False` - Sem Redis (opcional)
- `DATABASE_HOST=localhost` - Banco local/Docker

**Quando usar**: Desenvolvimento local, testes, debugging

---

### `.env.prod` - Produção
- `DEBUG=False` - Segurança (não expor erros)
- `EMAIL_BACKEND=smtp` - SMTP real (Postfix)
- `USE_REDIS=True` - Cache e sessões
- `DATABASE_HOST=localhost` - PostgreSQL produção

**Quando usar**: Servidor de produção (onkoto.com.br)

---

## 🔄 Fluxo de Carregamento

```
1. Django inicia → settings.py
2. Lê DJANGO_ENV do sistema operacional (default: 'development')
3. Escolhe arquivo: .env.dev ou .env.prod
4. Carrega variáveis do arquivo escolhido
5. Lê DEBUG do arquivo carregado
6. Configura aplicação conforme DEBUG
```

---

## ✅ Validação da Configuração

Execute o servidor e observe a mensagem inicial:

```bash
python manage.py runserver
```

**Saída esperada (dev):**
```
[CONFIG] Projeto: construtora | Ambiente: DEVELOPMENT | Arquivo: .env.dev
```

**Saída esperada (prod):**
```
[CONFIG] Projeto: construtora | Ambiente: PRODUCTION | Arquivo: .env.prod
```

---

## 🎯 Casos de Uso

### Caso 1: Desenvolvimento Local
```powershell
# Configurar uma vez (Windows)
[System.Environment]::SetEnvironmentVariable('DJANGO_ENV', 'development', 'User')

# Rodar aplicação
python manage.py runserver
# → Carrega .env.dev automaticamente
```

---

### Caso 2: Troubleshooting em Produção
```bash
# Servidor já configurado com DJANGO_ENV=production

# Editar temporariamente .env.prod
DEBUG=True  # ← Habilitar temporariamente

# Restart service
sudo systemctl restart construtora

# Testar problema
# ...

# IMPORTANTE: Reverter após troubleshooting
DEBUG=False
sudo systemctl restart construtora
```

---

### Caso 3: Servidor de Staging
```bash
# Criar .env.staging
cp .env.prod .env.staging
# Editar valores específicos

# Configurar variável de ambiente
export DJANGO_ENV=staging

# Atualizar settings.py para suportar 'staging'
```

---

## ⚠️ Segurança

1. **Nunca commitar arquivos `.env.*`** no Git
   - Adicionar ao `.gitignore`
   - Usar `.env.example` como template

2. **Produção sempre com `DEBUG=False`**
   - Expor stack traces = vazamento de informações sensíveis

3. **Separar credenciais por ambiente**
   - Senhas diferentes entre dev e prod
   - `SECRET_KEY` único e secreto em produção

4. **Validar `ALLOWED_HOSTS` em produção**
   - Nunca usar `*` (wildcard) em produção

---

## 🐛 Troubleshooting

### Erro: "Arquivo de ambiente não encontrado"
```
FileNotFoundError: Arquivo de ambiente não encontrado: f:\...\environments\.env.dev
Configure a variável DJANGO_ENV no sistema
```

**Solução**: Configure `DJANGO_ENV` conforme instruções acima.

---

### Erro: Variável não definida
```bash
# Verificar se DJANGO_ENV existe
echo $DJANGO_ENV  # Linux
$env:DJANGO_ENV   # Windows PowerShell
```

**Se vazio**: Configurar variável de ambiente.

---

### Ambiente errado carregado
```bash
# Verificar valor atual
echo $DJANGO_ENV

# Corrigir se necessário
export DJANGO_ENV=development  # Linux
[System.Environment]::SetEnvironmentVariable('DJANGO_ENV', 'development', 'User')  # Windows
```

**IMPORTANTE**: Reiniciar terminal/IDE após mudança!

---

## 📚 Referências

- **Django Documentation**: [Settings](https://docs.djangoproject.com/en/5.0/ref/settings/)
- **django-environ**: [Read the Docs](https://django-environ.readthedocs.io/)
- **12-Factor App**: [Config](https://12factor.net/config)
- **Projeto**: `.github/copilot-instructions.md`, seção 7.1

---

**Última atualização**: 16 de Janeiro de 2026  
**Responsável**: Configuração refatorada para separar `DJANGO_ENV` de `DEBUG`
