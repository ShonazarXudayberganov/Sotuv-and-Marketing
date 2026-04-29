#!/bin/bash
# NEXUS AI - One-command setup
# Bu skript boshlang'ich tuzilmani yaratadi.

set -e

echo "🚀 NEXUS AI o'rnatishni boshlamoqda..."

# Check requirements
command -v docker >/dev/null 2>&1 || { echo "❌ Docker o'rnatilmagan."; exit 1; }
command -v node >/dev/null 2>&1 || { echo "❌ Node.js o'rnatilmagan."; exit 1; }
command -v python3 >/dev/null 2>&1 || { echo "❌ Python 3 o'rnatilmagan."; exit 1; }

# Versions
NODE_VERSION=$(node -v | cut -d'v' -f2 | cut -d'.' -f1)
[ "$NODE_VERSION" -ge "20" ] || { echo "❌ Node.js 20+ kerak (joriy: $NODE_VERSION)"; exit 1; }

PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo "✓ Python $PYTHON_VERSION, Node $NODE_VERSION"

# Create .env if not exists
if [ ! -f .env ]; then
    echo "📝 .env fayli yaratilmoqda..."
    cp .env.example .env
    echo "⚠️  Iltimos .env faylini API kalitlar bilan to'ldiring!"
fi

# Start services
echo "🐳 Docker servislari ishga tushirilmoqda..."
docker-compose up -d postgres redis

# Wait for DB
echo "⏳ PostgreSQL'ni kutmoqda..."
sleep 5

# Backend setup
echo "🐍 Backend setup..."
cd apps/api
[ -d ".venv" ] || python3 -m venv .venv
source .venv/bin/activate
pip install poetry
poetry install
poetry run alembic upgrade head

# Create first admin (interactive)
echo ""
read -p "Admin yaratasizmi? (y/n): " CREATE_ADMIN
if [ "$CREATE_ADMIN" = "y" ]; then
    poetry run python scripts/create_admin.py
fi

cd ../..

# Frontend setup
echo "⚛️  Frontend setup..."
cd apps/web
npm install
cd ../..

echo ""
echo "✅ Tayyor!"
echo ""
echo "Ishga tushirish:"
echo "  Backend:  cd apps/api && poetry run uvicorn app.main:app --reload"
echo "  Frontend: cd apps/web && npm run dev"
echo ""
echo "Yoki Docker bilan: docker-compose up"
echo ""
echo "Brauzerda oching: http://localhost:3000"
