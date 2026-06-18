# Stage 1: Build the frontend application
# Usa uma imagem Node.js leve para instalar dependências e construir o projeto.
FROM node:20-alpine AS build

# Define o diretório de trabalho dentro do container para o frontend
WORKDIR /app/frontend

# Copia os arquivos de configuração do projeto (package.json e yarn.lock)
# Assume que estes arquivos estão na pasta 'frontend' do contexto de build.
COPY frontend/package.json frontend/yarn.lock ./

# Instala as dependências do projeto.
# '--frozen-lockfile' garante que a instalação use o yarn.lock exatamente como está.
RUN yarn install --frozen-lockfile

# Copia o restante dos arquivos do frontend para o diretório de trabalho.
COPY frontend/ .

# Executa o comando de build do frontend.
# Assume que o comando 'yarn build' gera os arquivos estáticos na pasta 'dist'.
RUN yarn build

# Stage 2: Serve a aplicação construída com Nginx
# Usa uma imagem Nginx leve para servir os arquivos estáticos.
FROM nginx:alpine AS production

# Copia a configuração personalizada do Nginx para Single Page Applications (SPAs).
# Esta configuração garante que o roteamento do lado do cliente funcione corretamente.
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf

# Copia os arquivos estáticos construídos do estágio 'build' para o diretório de serviço do Nginx.
COPY --from=build /app/frontend/dist /usr/share/nginx/html

# Expõe a porta 80, que é a porta padrão do Nginx.
EXPOSE 80

# Comando para iniciar o Nginx em primeiro plano.
CMD ["nginx", "-g", "daemon off;"]
