FROM nginx

COPY ./nginx.conf /etc/nginx/conf.d/default.conf
COPY ./chrome /usr/share/nginx/html/config/chrome
COPY ./chrome /usr/share/nginx/html/beta/config/chrome
COPY ./main.yml /usr/share/nginx/html/config/main.yml
COPY ./main.yml /usr/share/nginx/html/beta/config/main.yml
COPY ./api /usr/share/nginx/html/api
