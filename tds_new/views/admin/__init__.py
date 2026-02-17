"""
Views administrativas - Sistema TDS New
Week 8: Interface de gestão global do sistema

Requer permissão is_staff ou is_superuser
Diferença das views de usuário final:
- Usuário Final: vê apenas dados da sua conta (multi-tenant)
- Admin: vê dados de TODAS as contas (global)

Módulos:
- dashboard.py: Dashboard global com métricas consolidadas
- provisionamento.py: Gestão de certificados e alocação de gateways
- auditoria.py: Logs e compliance (Week 9)
- manutencao.py: Ferramentas de manutenção do sistema (Week 10)
"""
