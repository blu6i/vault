FROM nginx:1.27-alpine

# Устанавливаем curl для docker healthcheck
RUN apk add --no-cache curl

# Удаляем дефолтный конфиг
RUN rm -f /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]