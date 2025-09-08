FROM nginx:1.25-alpine

# Remove the default Nginx configuration file to ensure ours is used.
RUN rm /etc/nginx/conf.d/default.conf

# Copy the static frontend files to the Nginx public directory
COPY ./LGS_Stock_Frontend /usr/share/nginx/html

# Copy our custom reverse proxy configuration.
COPY ./LGS_Stock_Frontend/nginx.conf /etc/nginx/conf.d/default.conf

# Expose port 80
EXPOSE 80

# The default Nginx command will start the server
CMD ["nginx", "-g", "daemon off;"]