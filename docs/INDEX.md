# Documentation Index

Comprehensive documentation for the AI SOC multi-agent framework.

## Getting Started

**New to the project?** Start here:

1. [README.md](../README.md) - Project overview and quick start
2. [QUICK_REFERENCE.md](../QUICK_REFERENCE.md) - Essential commands at a glance
3. [DEPLOYMENT.md](../DEPLOYMENT.md) - Complete deployment guide

## Quick Links

### For Developers

- **Quick Start**: Run `./scripts/quick-start.sh`
- **Local Development**: See [docker-compose.override.yml.example](../docker-compose.override.yml.example)
- **API Reference**: See [ai_soc/](../ai_soc/)
- **Testing**: Run `./scripts/demo.sh`

### For Operators

- **Deployment Guide**: [DEPLOYMENT.md](../DEPLOYMENT.md)
- **Security Best Practices**: [SECURITY.md](../SECURITY.md)
- **Troubleshooting**: [TROUBLESHOOTING.md](../TROUBLESHOOTING.md)
- **Architecture**: [ARCHITECTURE.md](../ARCHITECTURE.md)

### For Security Teams

- **Security Practices**: [SECURITY.md](../SECURITY.md)
- **Incident Response**: [SECURITY.md](../SECURITY.md#incident-response)
- **Compliance**: [SECURITY.md](../SECURITY.md#compliance-considerations)

## Core Documentation

| Document | Description | Audience |
|----------|-------------|----------|
| [README.md](../README.md) | Project overview | Everyone |
| [DEPLOYMENT.md](../DEPLOYMENT.md) | Complete deployment guide | DevOps, SRE |
| [ARCHITECTURE.md](../ARCHITECTURE.md) | System architecture | Architects, Developers |
| [SECURITY.md](../SECURITY.md) | Security best practices | Security, DevOps |
| [TROUBLESHOOTING.md](../TROUBLESHOOTING.md) | Common issues and solutions | Everyone |
| [QUICK_REFERENCE.md](../QUICK_REFERENCE.md) | Quick command reference | Everyone |

## Scripts Documentation

- [scripts/README.md](../scripts/README.md) - Complete scripts documentation
- [scripts/bootstrap.sh](../scripts/bootstrap.sh) - Environment initialization
- [scripts/quick-start.sh](../scripts/quick-start.sh) - One-command deployment
- [scripts/demo.sh](../scripts/demo.sh) - Red→blue→purple demo

## Configuration

- [.env.example](../.env.example) - Environment variables template
- [docker-compose.yml](../docker-compose.yml) - Service orchestration
- [Makefile](../Makefile) - Common commands

## Workflows

### Initial Setup
```bash
./scripts/quick-start.sh
```

### Development
```bash
make dev
make logs
make test
```

### Production Deployment
See [DEPLOYMENT.md](../DEPLOYMENT.md#production-deployment-checklist)

## Service URLs (Default)

| Service | URL |
|---------|-----|
| Frontend | http://localhost:8000 |
| AI SOC API | http://localhost:9000 |
| MinIO Console | http://localhost:9001 |
| Vault UI | http://localhost:8200 |

## Support

1. Check [TROUBLESHOOTING.md](../TROUBLESHOOTING.md)
2. Review [GitHub Issues](https://github.com/perryjr1444-ux/jigglesmccrusty/issues)
3. Create new issue if needed

---

**Version**: 0.1.0  
**Last Updated**: 2025-10-05
