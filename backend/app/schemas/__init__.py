"""API request/response şemaları (Pydantic).

Tablo modelleri app/models'te; bunlar yalnızca API sınırındaki giriş/çıkış
sözleşmeleridir. Ayrım kasıtlı: DB şekli ile API şekli birbirinden bağımsız
evrilebilsin (örn. hashed_password asla dışarı sızmasın).
"""
