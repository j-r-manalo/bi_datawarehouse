# Use the official AWS Lambda Python 3.12 image
FROM public.ecr.aws/lambda/python:3.12

# Install build dependencies
RUN microdnf update -y && \
    microdnf install -y gcc gcc-c++ postgresql-devel zip

WORKDIR /tmp/build

# Create the exact directory structure Lambda expects
RUN mkdir -p python/lib/python3.12/site-packages

# Install only psycopg2-binary
RUN pip3 install --no-cache-dir --upgrade pip && \
    pip3 install --no-cache-dir --target python/lib/python3.12/site-packages psycopg2-binary

# Verify that psycopg2 is installed correctly
RUN cd /tmp && \
    python3 -c "import sys; sys.path.insert(0, '/tmp/build/python/lib/python3.12/site-packages'); import psycopg2; print(f'psycopg2 version: {psycopg2.__version__}')"

# Remove unnecessary files to reduce layer size
RUN find python -name "__pycache__" -type d -exec rm -rf {} +; exit 0
RUN find python -name "*.so" -exec strip {} \; ; exit 0
RUN find python -name "*.pyc" -delete
RUN find python -name "tests" -type d -exec rm -rf {} +; exit 0
RUN find python -name "*.egg-info" -exec rm -rf {} \; ; exit 0
RUN find python -name "*.dist-info" -type d -exec rm -rf {} +; exit 0

# Create a simple test file to verify the imports work
RUN echo 'import psycopg2; print(f"Successfully imported psycopg2 {psycopg2.__version__}")' > python/test_imports.py

# Zip the entire structure
RUN zip -r /orchestrator_layer.zip python

# Default command
CMD ["bash"]