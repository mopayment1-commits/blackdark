# BLACKDARK Kubernetes templates

Roadmap-ready manifests for institutional scale-out (report Flaw 5).

## Apply order

```bash
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml
cp k8s/secret.example.yaml k8s/secret.yaml   # edit real values — do not commit
kubectl apply -f k8s/secret.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/hpa.yaml
kubectl apply -f k8s/pdb.yaml
kubectl apply -f k8s/ingress.yaml            # optional / cluster-specific
```

## Notes

- Image: build/push your registry tag and set `image:` in `deployment.yaml`.
- Postgres + Redis should run as managed services (or separate Helm charts), not inside the web pod.
- Production guard requires `DATABASE_URL`, `REDIS_URL`, `SECRETS_MASTER_KEY`, `SESSION_TOKEN_PEPPER`, `ADMIN_TOTP_SECRET`.
- HPA targets 2→20 replicas for horizontal scale evidence toward large concurrent audiences.
