FROM ubuntu
RUN apt-get install -y openssh-server
RUN mkdir -p /var/run/sshd
CMD /usr/sbin/sshd -D -e
EXPOSE 22
