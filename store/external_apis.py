"""
Servicio de integraciones con APIs externas.
"""
import requests
from django.core.cache import cache
import logging

logger = logging.getLogger(__name__)

LASTFM_API_KEY = "b25b959554ed76058ac220b7b2e0a026"  # Free tier key (demo)
LASTFM_BASE_URL = "http://ws.audioscrobbler.com/2.0/"


def get_instrument_info_from_lastfm(instrument_name: str):
    """
    Obtiene información sobre un instrumento desde Last.fm API.
    Intenta buscar artistas que toquen ese instrumento y obtener el género predominante.
    
    Args:
        instrument_name: Nombre del instrumento (ej: "Guitarra Fender")
    
    Returns:
        dict con información adicional o {} si no hay resultados
    """
    # Cachear por 24 horas
    cache_key = f"lastfm_instrument_{instrument_name.lower()}"
    cached = cache.get(cache_key)
    if cached is not None:
        logger.info(f"Cache hit para {instrument_name}: {cached}")
        return cached

    try:
        # Extraer término de búsqueda (primera palabra)
        search_term = instrument_name.split()[0].lower()  # Primera palabra (p.ej "Guitarra")
        logger.info(f"Buscando en Last.fm: {search_term}")
        
        # Usar tag.getinfo en lugar de tag.search (que no existe en el API)
        # Vamos a intentar varios alias comunes del instrumento
        possible_tags = [
            search_term,  # "guitarra"
            search_term + "s",  # "guitarras" 
            "played with " + search_term,  # Algunos instrumentos se buscan así
        ]
        
        result = None
        
        for tag_name in possible_tags:
            try:
                params = {
                    "method": "tag.getinfo",
                    "tag": tag_name,
                    "api_key": LASTFM_API_KEY,
                    "format": "json",
                }

                response = requests.get(LASTFM_BASE_URL, params=params, timeout=5)
                
                if response.status_code == 200:
                    data = response.json()
                    logger.info(f"Last.fm response para {tag_name}: {data}")

                    if "tag" in data and data["tag"]:
                        tag = data["tag"]
                        result = {
                            "tag_name": tag.get("name"),
                            "url": tag.get("url"),
                            "reach": tag.get("reach"),
                            "taggings": tag.get("total"),
                        }
                        logger.info(f"Found tag data: {result}")
                        cache.set(cache_key, result, 60 * 60 * 24)  # 24 horas
                        return result
            except Exception as e:
                logger.debug(f"Error trying tag {tag_name}: {e}")
                continue
        
        logger.warning(f"No tags found for {instrument_name}")
        cache.set(cache_key, {}, 60 * 60 * 24)  # Cache empty result too
        return {}

    except Exception as e:
        logger.error(f"Error consultando Last.fm para {instrument_name}: {e}")
        cache.set(cache_key, {}, 3600)  # Cache error for 1 hour
        return {}


def get_top_artists_by_tag(tag_name: str, limit: int = 5):
    """
    Obtiene los artistas top para un tag específico.
    
    Args:
        tag_name: Nombre del tag/género
        limit: Cantidad de artistas a retornar
    
    Returns:
        Lista de artistas o []
    """
    cache_key = f"lastfm_artists_{tag_name.lower()}_{limit}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    try:
        params = {
            "method": "tag.gettopartists",
            "tag": tag_name.lower(),
            "limit": limit,
            "api_key": LASTFM_API_KEY,
            "format": "json",
        }

        response = requests.get(LASTFM_BASE_URL, params=params, timeout=5)
        response.raise_for_status()

        data = response.json()

        if "topartists" in data and "artist" in data["topartists"]:
            artists = data["topartists"]["artist"]
            if artists:
                result = [
                    {
                        "name": a.get("name"),
                        "mbid": a.get("mbid"),
                        "playcount": a.get("playcount"),
                        "url": a.get("url"),
                    }
                    for a in (artists if isinstance(artists, list) else [artists])
                ]
                cache.set(cache_key, result, 60 * 60 * 24)
                return result

        logger.warning(f"No artists found for tag {tag_name}")
        cache.set(cache_key, [], 60 * 60 * 24)
        return []

    except Exception as e:
        logger.error(f"Error consultando artistas Last.fm para {tag_name}: {e}")
        cache.set(cache_key, [], 3600)
        return []


def get_instrument_origin_from_wikipedia(instrument_name: str) -> str:
    """
    Obtiene el país de origen de un instrumento desde Wikipedia API.
    También detecta marcas conocidas de instrumentos.
    
    Args:
        instrument_name: Nombre del instrumento (ej: "Guitarra", "Fender Guitarra", "Takamine")
    
    Returns:
        Nombre del país de origen o string vacío si no se encuentra
    """
    if not instrument_name or not instrument_name.strip():
        return ""
    
    # Marcas conocidas de instrumentos
    brand_origins = {
        # Guitarras
        "fender": "Estados Unidos",
        "gibson": "Estados Unidos",
        "martin": "Estados Unidos",
        "taylor": "Estados Unidos",
        "ibanez": "Japón",
        "takamine": "Japón",
        "yamaha": "Japón",
        "epiphone": "Estados Unidos",
        "squire": "Estados Unidos",
        "washburn": "Estados Unidos",
        "ovation": "Estados Unidos",
        "cort": "Corea del Sur",
        "schecter": "Estados Unidos",
        "kalamazoo": "Estados Unidos",
        "alvarez": "México",
        "alhambra": "España",
        "admira": "España",
        "manuel rodriguez": "España",
        "ramirez": "España",
        "flamenco": "España",
        # Otros instrumentos
        "stradivarius": "Italia",
        "guarneri": "Italia",
        "amati": "Italia",
        "steinway": "Estados Unidos",
        "kawai": "Japón",
        "roland": "Japón",
        "korg": "Japón",
        "nord": "Suecia",
        "moog": "Estados Unidos",
        "behringer": "Alemania",
        "akai": "Japón",
        "pioneer": "Japón",
        "technics": "Japón",
        "shure": "Estados Unidos",
        "neumann": "Alemania",
        "rode": "Australia",
        "sennheiser": "Alemania",
        "audiotechnica": "Japón",
    }
    
    instrument_lower = instrument_name.lower().strip()
    
    # Primero, buscar marcas conocidas
    for brand, origin in brand_origins.items():
        if brand in instrument_lower:
            logger.info(f"Found brand {brand} in {instrument_name}, origin: {origin}")
            return origin
    
    cache_key = f"wikipedia_instrument_origin_{instrument_lower}"
    cached = cache.get(cache_key)
    if cached is not None:
        logger.info(f"Cache hit para origen de {instrument_name}: {cached}")
        return cached
    
    try:
        # Buscar en Wikipedia en español primero
        wikipedia_api_url = "https://es.wikipedia.org/w/api.php"
        
        params = {
            "action": "query",
            "format": "json",
            "titles": instrument_name.capitalize(),
            "prop": "extracts",
            "explaintext": True,
            "redirects": 1,
        }
        
        response = requests.get(wikipedia_api_url, params=params, timeout=5)
        response.raise_for_status()
        
        data = response.json()
        pages = data.get("query", {}).get("pages", {})
        
        if not pages:
            logger.warning(f"No Wikipedia page found for {instrument_name}")
            cache.set(cache_key, "", 60 * 60 * 24)
            return ""
        
        # Obtener el primer (y único) resultado
        page = next(iter(pages.values()))
        extract = page.get("extract", "").lower()
        
        if not extract:
            logger.warning(f"No extract found for {instrument_name}")
            cache.set(cache_key, "", 60 * 60 * 24)
            return ""
        
        # Palabras clave por país/región (puedes expandir esto)
        country_keywords = {
            "españa": "España",
            "brasil": "Brasil",
            "italia": "Italia",
            "méxico": "México",
            "argentina": "Argentina",
            "perú": "Perú",
            "cuba": "Cuba",
            "alemania": "Alemania",
            "francia": "Francia",
            "américa latina": "América Latina",
            "américa": "América",
            "europa": "Europa",
            "áfrica": "África",
            "asia": "Asia",
            "estados unidos": "Estados Unidos",
            "eeuu": "Estados Unidos",
            "usa": "Estados Unidos",
            "Inglaterra": "Inglaterra",
            "irlanda": "Irlanda",
            "portugal": "Portugal",
            "japón": "Japón",
            "china": "China",
            "india": "India",
            "grecia": "Grecia",
            "turquía": "Turquía",
            "rusia": "Rusia",
            "africa": "África",
            "norteamérica": "Norteamérica",
            "centroamérica": "Centroamérica",
            "sudamérica": "Sudamérica",
            "australia": "Australia",
            "corea": "Corea",
            "suecia": "Suecia",
        }
        
        # Buscar en el texto
        origin = ""
        for keyword, country in country_keywords.items():
            if keyword in extract:
                origin = country
                # Priorizar búsqueda en las primeras líneas
                if keyword in extract[:500]:
                    break
        
        if origin:
            logger.info(f"Found origin for {instrument_name}: {origin}")
            cache.set(cache_key, origin, 60 * 60 * 24)
            return origin
        
        logger.warning(f"Could not determine origin for {instrument_name} from Wikipedia")
        cache.set(cache_key, "", 60 * 60 * 24)
        return ""
        
    except Exception as e:
        logger.error(f"Error consultando Wikipedia para {instrument_name}: {e}")
        cache.set(cache_key, "", 3600)
        return ""
