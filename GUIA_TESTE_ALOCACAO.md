# 🎯 GUIA DE TESTE: Interface de Alocação de Gateways

**Data:** 17/02/2026  
**Status do Banco:** ✅ 2 Certificados Criados  
**Servidor:** http://localhost:8000

---

## ❌ PROBLEMA IDENTIFICADO

**Causa Raiz:** Banco de dados **SEM CERTIFICADOS**

A interface de alocação é acessada pela **lista de certificados**. Como não havia certificados no banco, a lista estava vazia e o botão "Alocar" não aparecia.

---

## ✅ SOLUÇÃO APLICADA

Foram criados **2 certificados de teste** para os gateways existentes:

### Certificados Criados:

| Gateway | MAC Address | Serial Number | Validade | Conta |
|---------|-------------|---------------|----------|-------|
| GW001 | aa:bb:cc:dd:ee:01 | TEST-AABBCCDDEE01-20260217175234 | 15/02/2036 | Conta Teste - Desenvolvimento |
| GW002 | aa:bb:cc:dd:ee:02 | TEST-AABBCCDDEE02-20260217175234 | 15/02/2036 | Conta Teste - Desenvolvimento |

---

## 🧪 TESTE PASSO A PASSO

### **Passo 1: Acessar Lista de Certificados** 🔗

1. Abrir navegador
2. Acessar: http://localhost:8000/tds_new/admin-sistema/provisionamento/certificados/
3. **Login necessário:** Use usuário com `is_staff=True` ou `is_superuser=True`

**Resultado Esperado:**
- ✅ Lista com **2 certificados** visíveis
- ✅ Cada linha tem coluna **"Ações"** à direita
- ✅ Botão **"Alocar"** azul ao lado de cada certificado

---

### **Passo 2: Clicar no Botão "Alocar"** 📝

1. Localizar certificado `TEST-AABBCCDDEE01-...`
2. Clicar no botão **"Alocar"** (azul, com ícone ↔)

**URL Esperada:**
```
http://localhost:8000/tds_new/admin-sistema/provisionamento/alocar/1/
```

**Tela Esperada:**
```
┌──────────────────────────────────────────────────────────────┐
│  🔐 Alocar Gateway: aa:bb:cc:dd:ee:01                        │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  📊 INFORMAÇÕES DO GATEWAY                                   │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ Código: GW001                                          │ │
│  │ Nome: Gateway Sede Principal                           │ │
│  │ MAC Address: aa:bb:cc:dd:ee:01                         │ │
│  │ Conta Atual: Conta Teste - Desenvolvimento            │ │
│  │ Status: [Online/Offline]                               │ │
│  │ Dispositivos: X dispositivo(s) vinculado(s)            │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  🔐 CERTIFICADO X.509                                        │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ Serial Number: TEST-AABBCCDDEE01-20260217175234        │ │
│  │ Expira em: 15/02/2036                                  │ │
│  │ Status: [Válido]                                       │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  📝 SELECIONAR CONTA DESTINO                                 │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ Conta Destino: [Dropdown com contas ativas] *         │ │
│  │                                                        │ │
│  │ ☑ Transferir dispositivos vinculados                  │ │
│  │   Se marcado, todos os dispositivos vinculados ao     │ │
│  │   gateway também serão transferidos para a nova conta │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  📋 RESUMO DA OPERAÇÃO                                       │
│  • Gateway aa:bb:cc:dd:ee:01 será transferido              │
│  • Certificado X.509 será atualizado automaticamente       │
│  • X dispositivo(s) serão transferidos junto (se marcado)  │
│                                                              │
│  [Cancelar]                              [Alocar Gateway]   │
└──────────────────────────────────────────────────────────────┘
```

---

### **Passo 3: Testar Alocação** ✅

**Cenário 1: Alocar para mesma conta (sem mudança)**
1. Selecionar "Conta Teste - Desenvolvimento"
2. Clicar "Alocar Gateway"
3. **Resultado:** Deve processar normalmente (sem erro)

**Cenário 2: Transferir para outra conta (se houver)**
1. Criar nova conta via admin Django
2. Selecionar a nova conta no dropdown
3. Marcar/desmarcar checkbox "Transferir dispositivos"
4. Clicar "Alocar Gateway"
5. **Resultado:** 
   - Mensagem de sucesso: ✅ "Gateway aa:bb:cc:dd:ee:01 transferido de 'Conta A' → 'Conta B'"
   - Redirecionamento para lista de certificados

---

## 🔍 VERIFICAÇÕES ADICIONAIS

### **Console do Navegador (F12)**
Verificar se há erros JavaScript:
- ❌ Se houver erros, reportar no chat
- ✅ Se não houver erros, tudo OK

### **Botão "Alocar" Não Aparece?**

**Verificações:**
1. ✅ Certificados existem no banco? (Execute `python diagnostico_alocacao.py`)
2. ✅ Gateway existe com MAC correspondente?
3. ✅ Template carregado corretamente?
4. ✅ View `get_context_data()` adiciona `cert.gateway`?

### **Erro 404 ao Clicar no Botão?**

**Verificações:**
1. ✅ URL correta: `/tds_new/admin-sistema/provisionamento/alocar/{gateway_id}/`
2. ✅ Rota registrada em `urls.py`
3. ✅ View `alocar_gateway_view` importada corretamente

### **Erro 500 ao Submeter Formulário?**

**Possíveis causas:**
1. ❌ Campo `Conta.nome` não existe (deve ser `Conta.name`)
2. ❌ Certificado não encontrado para o MAC
3. ❌ Transação falhou (rollback automático)

**Solução:** Verificar logs do servidor Django no terminal

---

## 📊 SCRIPTS DE DIAGNÓSTICO

### **Verificar Estado do Banco:**
```bash
python diagnostico_alocacao.py
```

### **Criar Certificados (se necessário):**
```bash
python criar_certificados_teste.py
```

### **Validar URLs e Templates:**
```bash
python validacao_week9_fase1.py
```

---

## ✅ CHECKLIST DE VALIDAÇÃO

- [ ] Servidor Django rodando em http://localhost:8000
- [ ] Login com usuário staff/superuser
- [ ] Lista de certificados carrega com 2 certificados
- [ ] Botão "Alocar" visível na coluna "Ações"
- [ ] Clicar em "Alocar" leva para página de alocação
- [ ] Formulário carrega informações do gateway
- [ ] Dropdown de contas funciona
- [ ] Checkbox "Transferir dispositivos" funciona
- [ ] Botão "Alocar Gateway" funciona
- [ ] Mensagem de sucesso aparece após submissão
- [ ] Redirecionamento para lista de certificados OK
- [ ] Gateway.conta_id foi atualizado no banco
- [ ] CertificadoDevice.conta_id foi atualizado

---

## 🚀 PRÓXIMAS AÇÕES

Após validar que a interface funciona:

1. **Commit da implementação completa**
2. **Iniciar Week 9 - Fase 2:** Importação CSV em lote
3. **Iniciar Week 9 - Fase 3:** Revogação de certificados
4. **Iniciar Week 9 - Fase 4:** Auditoria com LogEntry

---

## 📞 SUPORTE

Se a interface ainda não aparecer após criar certificados:

1. **Compartilhar prints** da tela no navegador
2. **Compartilhar logs** do servidor Django no terminal
3. **Executar diagnóstico** e compartilhar output:
   ```bash
   python diagnostico_alocacao.py > diagnostico.txt
   ```

---

**Status do Sistema:**
- ✅ Implementação completa (Week 9 - Fase 1)
- ✅ Certificados criados (2 registros)
- ✅ Servidor rodando (porta 8000)
- 🧪 **Aguardando testes manuais do usuário**
