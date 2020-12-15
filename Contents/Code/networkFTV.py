import PAsearchSites
import PAgenres
import PAactors
import PAutils


def search(results, encodedTitle, searchTitle, siteNum, lang, searchDate):
    sceneID = None
    splited = searchTitle.split(' ')
    searchResults = []

    if unicode(splited[0], 'UTF-8').isdigit():
        sceneID = splited[0]
        searchTitle = searchTitle.replace(sceneID, '', 1).strip()
        directURL = PAsearchSites.getSearchSearchURL(siteNum) + sceneID + '.html'

        searchResults.append(directURL)

    googleResults = PAutils.getFromGoogleSearch(searchTitle, siteNum)
    for sceneURL in googleResults:
        if ('/update/' in sceneURL) and sceneURL not in searchResults:
            searchResults.append(sceneURL)

    for sceneURL in searchResults:
        req = PAutils.HTTPRequest(sceneURL)
        detailsPageElements = HTML.ElementFromString(req.text)

        curID = PAutils.Encode(sceneURL)
        titleDate = detailsPageElements.xpath('//title')[0].text_content().split('Released')
        titleNoFormatting = titleDate[0].strip()

        date = titleDate[-1].replace('!', '').strip()
        releaseDate = parse(date).strftime('%Y-%m-%d')

        if searchDate:
            score = 100 - Util.LevenshteinDistance(searchDate, releaseDate)
        else:
            score = 100 - Util.LevenshteinDistance(searchTitle.lower(), titleNoFormatting.lower())

        results.Append(MetadataSearchResult(id='%s|%d' % (curID, siteNum), name='%s [%s] %s' % (titleNoFormatting, PAsearchSites.getSearchSiteName(siteNum), releaseDate), score=score, lang=lang))

    return results


def update(metadata, siteID, movieGenres, movieActors):
    metadata_id = str(metadata.id).split('|')
    sceneURL = PAutils.Decode(metadata_id[0])
    
    req = PAutils.HTTPRequest(sceneURL)
    detailsPageElements = HTML.ElementFromString(req.text)

    # Title
    titleDate = detailsPageElements.xpath('//title')[0].text_content().split('Released')
    metadata.title = titleDate[0].strip()

    # Summary
    metadata.summary = detailsPageElements.xpath('//div[@id="Bio"]')[0].text_content().strip()

    # Studio
    metadata.studio = 'First Time Videos'

    # Tagline and Collection(s)
    metadata.collections.clear()
    tagline = PAsearchSites.getSearchSiteName(siteID).strip()
    metadata.tagline = tagline
    metadata.collections.add(tagline)

    # Release Date
    date = titleDate[-1].replace('!', '').strip()
    if date:
        date_object = parse(date)
        metadata.originally_available_at = date_object
        metadata.year = metadata.originally_available_at.year

    # Genres
    movieGenres.clearGenres()
    genres = []
    if tagline == 'FTVGirls'.lower():
        genres = ['Teen', 'Solo', 'Public']
    elif tagline == 'FTVMilfs'.lower():
        genres = ['MILF', 'Solo', 'Public']

    for genreName in genres:
        movieGenres.addGenre(genreName)

    # Actors
    movieActors.clearActors()
    idx = 0
    actors = []
    try:
        sceneID = int(re.search(r'(?<=-)\d.*(?=\.)', sceneURL).group(0))
    except:
        sceneID = 0

    for actorLink in detailsPageElements.xpath('//div[@id="ModelDescription"]//h1'):
        actorName = actorLink.text_content().strip().replace('\'s Statistics', '')
        actors.append(actorName)

        regex = re.search(r'\s(%s [A-Z]\w{1,})\s' % actorName, metadata.summary)
        if regex:
            actorName = regex.group(1)

        actorPhotoURL = detailsPageElements.xpath('//div[@id="Thumbs"]/img/@src')[idx]
        
        movieActors.addActor(actorName, actorPhotoURL)
        idx += 1

    # Posters
    art = []
    xpaths = [
        '//img[@id="Magazine"]/@src',
        '//div[@class="gallery"]//div[@class="row"]//@href',
        '//div[@class="thumbs_horizontal"]//@href',
        '//a[img[@class="t"]]/@href',
    ]

    scenes = photoLookup(sceneID)
    googleResults = PAutils.getFromGoogleSearch(' '.join(actors).strip(), siteID)
    for photoURL in googleResults:
        for scene in scenes:
            if (('galleries' in photoURL or 'preview' in photoURL) and (scene in photoURL or scene == 'none')):
                req = PAutils.HTTPRequest(photoURL)
                photoPageElements = HTML.ElementFromString(req.text)
                for xpath in xpaths:
                    for img in photoPageElements.xpath(xpath):
                        art.append(img)

    for xpath in xpaths:
        for img in detailsPageElements.xpath(xpath):
            art.append(img)

    Log('Artwork found: %d' % len(art))
    for idx, posterUrl in enumerate(art, 1):
        if not PAsearchSites.posterAlreadyExists(posterUrl, metadata):
            # Download image file for analysis
            try:
                image = PAutils.HTTPRequest(posterUrl, headers={'Referer': 'http://www.google.com'})
                im = StringIO(image.content)
                resized_image = Image.open(im)
                width, height = resized_image.size
                # Add the image proxy items to the collection
                if width > 1 or height > width:
                    # Item is a poster
                    metadata.posters[posterUrl] = Proxy.Media(image.content, sort_order=idx)
                if width > 100 and width > height:
                    # Item is an art item
                    metadata.art[posterUrl] = Proxy.Media(image.content, sort_order=idx)
            except:
                pass

    return metadata


def photoLookup(sceneID):
    if sceneID == 226:
        scenes = ['cool-colors', 'shes-on-fire', 'heating-up']
    elif sceneID == 210:
        scenes = ['supersexy-vixen', 'satin-sensuality', 'outdoor-finale']
    elif sceneID == 130:
        scenes = ['elegantly-sexual']
    elif sceneID == 1569:
        scenes = ['model-like-no-other', 'teen-penetration']
    elif sceneID == 1524:
        scenes = ['petite-gaping', 'penetration-limits']
    elif sceneID == 1573 or sceneID == 283:
        scenes = []
    else:
        scenes = ['none']

    return scenes
