FROM huggingface/transformers-pytorch-gpu

WORKDIR /code/

COPY requirements.txt /code/requirements.txt

COPY notebooks/. /code/notebooks/.

RUN pip3 install -r requirements.txt

RUN pip3 install jupyter

CMD ["jupyter", "notebook", "--port=8888", "--ip=0.0.0.0", "--allow-root"]
