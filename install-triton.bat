set GRADIO_SERVER_NAME=0.0.0.0
set PATH=.venv;.venv\Scripts;%PATH%

:: Check Triton Windows GPU Compatibility
:: https://github.com/triton-lang/triton-windows?tab=readme-ov-file#1-gpu
::
:: GPU Compatibility Table for Triton Windows
::
:: | RTX Version       | Architecture | SM   | Triton Version        | Notes                                                           |
:: | ----------------- | ------------ | ---- | --------------------- | ----------------------------------------------------------------|
:: | RTX 50xx          | Blackwell    | 120  | >= 3.3                | Requires PyTorch >= 2.7, CUDA >= 12.8                           |
:: | RTX 40xx          | Ada          | 89   | Official support      |                                                                 |
:: | RTX 30xx          | Ampere       | 86   | Official support      | fp8 supported in `triton-windows >= 3.5.0.post21`               |
:: | GTX 16xx/RTX 20xx | Turing       | 75   | <= 3.2                | fp8 supported in `triton-windows 3.2.0.post21`; dropped in 3.3+ |
:: | GTX 10xx+older    | Pascal+      | 61   | Not supported         |


python -m pip install "triton-windows>=3.5.0.post21"

pause
