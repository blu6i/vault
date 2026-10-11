FROM postgres:18-bookworm

# Устанавливаем русскую и UTF-8 локали
RUN apt-get update && apt-get install -y --no-install-recommends \
    locales \
    && rm -rf /var/lib/apt/lists/* \
    && localedef -i ru_RU -c -f UTF-8 -A /usr/share/locale/locale.alias ru_RU.UTF-8

ENV LANG=ru_RU.utf8

# Скрипты инициализации и кастомный конфиг
# (initdb/*.sql монтируются через volumes в compose.yaml)