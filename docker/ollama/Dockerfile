FROM ollama/ollama

COPY ./ollama/entrypoint.sh /entrypoint.sh

RUN chmod +x /entrypoint.sh

EXPOSE 11434
ENTRYPOINT ["/bin/sh", "/entrypoint.sh"]