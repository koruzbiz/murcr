# Derleme özelleştirmeleri
# Mümkün olduğunca sconstruct veya manifest dosyaları yerine bu dosyayı değiştirin.

from site_scons.site_tools.NVDATool.typings import AddonInfo, BrailleTables, SymbolDictionaries

# `addon_info` içindeki bazı dizeler çevrilebilir olduğundan,  bu dizeleri .po dosyalarına dahil etmemiz gerekir.  Gettext yalnızca `_` fonksiyonuna parametre olarak verilen dizeleri tanır.  Bu modülde çevirileri başlatmaktan kaçınmak için, argümanı olduğu gibi döndüren "sahte" bir `_` fonksiyonunu yalnızca içe aktarıyoruz.

from site_scons.site_tools.NVDATool.utils import _


# Eklenti bilgi değişkenleri
addon_info = AddonInfo(
	# Eklentinin adı/kimliği, NVDA için dahili
	addon_name="KoruzBiz_Murcr",
	# Eklenti özeti/başlığı, genelde kullanıcıya görünen eklenti adı
	# Çevirmenler: Eklenti yüklemesinde ve eklenti mağazasında gösterilecek
	# bu eklenti için özet/başlık
	#! "Körüz.biz MurCr – Erişilebilir Ses ve Video Kırpma ve Oluşturma"
	addon_summary=_("Koruz.biz MurCr – Accessible Audio & Video Trimming and Creation"),
	# Eklenti açıklaması
	# Çevirmenler: Eklenti mağazasındaki eklenti bilgi ekranında gösterilecek uzun açıklama
	#! "MurCr, görme engelli kullanıcılar için geliştirilmiş, tamamen erişilebilir bir ses ve video kırpma, oluşturma ve dönüştürme uygulamasıdır. Bu NVDA eklentisi, NVDA ile MurCr arasında bir köprü görevi görür. Dosyaları kırpmanıza, eşit parçalara ayırmanıza, farklı formatlara dönüştürmenize veya seçtiğiniz herhangi bir görüntüyü kullanarak videolar oluşturmanıza olanak tanır."
	addon_description=_("""MurCr is a fully accessible audio and video trimming, creation, and conversion application developed for blind users. This NVDA add-on acts as a bridge between NVDA and MurCr. It allows you to trim files, split them into equal parts, convert them to different formats, or create videos using any image you choose."""),
	# sürüm
	addon_version="2.6.2",
	# Bu sürüm için kısa değişiklik günlüğü
	# Çevirmenler: Eklenti mağazasında gösterilecek bu eklenti sürümü için "yenilikler" içeriği
	#! "MurCr, birçok farklı formattaki ses ve video dosyalarını işlemenize olanak sağlar. Zaman çizelgesi çakışması tespiti, video çözünürlüğü çakışması analizi ve diğer akıllı yönetim araçları gibi özelliklerle hata riskini azaltır. Tamamen erişilebilir arayüzü herkes için kullanılabilirlik sağlar."
	addon_changelog=_("""MurCr allows you to process audio and video files in many different formats. It reduces the risk of errors with features such as timeline overlap detection, video resolution conflict analysis, and other smart management tools. Its fully accessible interface ensures usability for everyone."""),
	# Yazar(lar)
	addon_author="Murat Kefeli <bilgi@koruz.biz>",
	# Eklenti dokümantasyon desteği için URL
	addon_url="https://MurText.org",
	# Kaynak kodunun bulunabileceği eklenti deposu URL’si
	addon_sourceURL=None,
	# Dokümantasyon dosya adı
	addon_docFileName="readme.html",
	# Desteklenen minimum NVDA sürümü (örn. "2019.3.0", minor sürüm isteğe bağlı)
	addon_minimumNVDAVersion="2022.1",
	# Desteklenen/test edilmiş son NVDA sürümü (örn. "2025.3.0", ideal olarak minimumdan daha yeni)
	addon_lastTestedNVDAVersion="2025.3",
	# Eklenti güncelleme kanalı (varsayılan None: kararlı sürümler,
	# geliştirme sürümleri için "dev" kullanın.)
	# Ne yaptığınızdan emin değilseniz değiştirmeyin!
	addon_updateChannel=None,
	# Eklenti lisansı (örn. GPL 2)
	addon_license=None,
	# Eklentinin lisanslandığı lisans belgesi için URL
	addon_licenseURL=None,
)

# Eklentinizin kaynaklarını oluşturan Python dosyalarını tanımlayın.
# Her dosyayı tek tek listeleyebilir (yol ayırıcı olarak "/" kullanarak)
# veya glob desenleri kullanabilirsiniz.
# Örneğin eklentinizin "globalPlugins" klasöründeki tüm ".py" dosyalarını dahil etmek için
# listeyi şu şekilde yazabilirsiniz:
# pythonSources = ["addon/globalPlugins/KoruzBiz_Murcr/*.py"]
# SCons Glob ifadeleri hakkında daha fazla bilgi için:
# https://scons.org/doc/production/HTML/scons-user/apd.html
pythonSources: list[str] = ["addon/globalPlugins/*.py"]

# Çeviri için dize içeren dosyalar. Genellikle Python kaynak dosyalarınız
i18nSources: list[str] = pythonSources + ["buildVars.py"]

# nvda-addon dosyası oluşturulurken yoksayılacak dosyalar
# Yollar, eklenti kaynaklarınızın kök dizinine değil eklenti dizinine göredir.
# Her dosyayı tek tek listeleyebilir (yol ayırıcı olarak "/")
# veya glob desenleri kullanabilirsiniz.
excludedFiles: list[str] = []

# NVDA eklentisi için temel dil  Eklentiniz İngilizce dışında bir dille yazılmışsa bu değişkeni düzenleyin.  Örneğin eklentiniz ağırlıklı olarak İspanyolca ise baseLanguage değerini "es" yapın.  Ayrıca yoksayılacak temel dil dosyalarını belirtmek için .gitignore dosyasını da düzenlemelisiniz. 
baseLanguage: str = "en"

# Eklenti dokümantasyonu için Markdown eklentileri  Çoğu eklenti ek Markdown eklentilerine ihtiyaç duymaz.  Tablolar gibi biçemlere destek eklemeniz gerekiyorsa aşağıdaki listeyi doldurun.  Uzantı dizeleri "markdown.extensions.uzantiAdi" biçiminde olmalıdır  örn. tablolar eklemek için "markdown.extensions.tables".
markdownExtensions: list[str] = []

# Özel braille çeviri tabloları
# Eklentiniz özel braille tabloları içeriyorsa (çoğu içermez) bu sözlüğü doldurun.
# Her anahtar braille tablo dosya adına göre adlandırılmış bir sözlüktür,
# içindeki anahtarlar şu öznitelikleri belirtir:
# displayName (kullanıcılara gösterilen ve çevrilebilir tablo adı),
# contracted (kısaltmalı (True) ya da kısaltmasız (False) braille kodu),
# output (çıktı tablo listesinde gösterimi),
# input (girdi tablo listesinde gösterimi).
brailleTables: BrailleTables = {}

# Özel konuşma sembol sözlükleri
# Sembol sözlüğü dosyaları locale klasöründe bulunur, örn. `locale\en`, ve `symbols-<ad>.dic` şeklinde adlandırılır.
# Eklentiniz özel konuşma sembol sözlükleri içeriyorsa (çoğu içermez) bu sözlüğü doldurun.
# Her anahtar sözlüğün adıdır,
# içindeki anahtarlar şu öznitelikleri belirtir:
# displayName (kullanıcılara gösterilen ve çevrilebilir sözlük adı),
# mandatory (Her zaman etkinse True, değilse False).
symbolDictionaries: SymbolDictionaries = {}
