# Chat with local AI

## Starting the app

```bash
cd frontend
```

### Install dependencies
```bash
# npm
npm install

# pnpm
pnpm install

# yarn
yarn install

# bun
bun install
```

### Run app
```bash
# npm
npm run start-app

# pnpm
pnpm start-app

# yarn
yarn start-app

# bun
bun run start-app
```

## Or run each module separately

### Nuxt app
```bash
cd frontend

# npm
npm rundev

# pnpm
pnpm dev

# yarn
yarn dev

# bun
bun run dev
```

### Docker (from the /frontend directory)
```bash
# npm
npm run start-docker

# pnpm
pnpm start-docker

# yarn
yarn start-docker

# bun
bun run start-docker
```

### Django server (from the main directory)
```bash
cd django_server

# start virtual environment (on Windows)
venv/Scripts/activate

# start virtual environment (on Linux/MacOs)
source venv/bin/activate

# install packages
pip install -r requirements.txt

# before first start of the server
# in code editor go to venv/Lib/site-packages/djongo/models/fields.py

# change
def from_db_value(self, value, expression, connection, context):
    return self.to_python(value)

# to
def from_db_value(self, value, expression, connection, context=False):
    return self.to_python(value)

# run server
python manage.py runserver
```