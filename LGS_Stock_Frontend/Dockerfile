FROM nginx:1.25-alpine

# Copy the static frontend files to the Nginx public directory
COPY ./LGS_Stock_Frontend /usr/share/nginx/html

# Expose port 80
EXPOSE 80

# The default Nginx command will start the server
CMD ["nginx", "-g", "daemon off;"]