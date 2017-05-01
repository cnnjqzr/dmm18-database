# coding=utf-8
import MySQLdb
import scrapy
import re


class DmmSpider(scrapy.Spider):
    name = "dmmspider"

    def start_requests(self):
        urls = self.retrieve_links('SELECT link FROM dmm18.video_links')
        # urls = ['http://www.dmm.co.jp/digital/videoa/-/detail/=/cid=oae00101/']
        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse_video)

    # extract alphabet links and make new requests
    def parse_alphabet_links(self, response):
        # extract alphabet links
        alphabet_links = response.css('table.menu_aiueo td a::attr(href)').extract()
        # make new requests
        # self.log(len(alphabet_links))
        for url in alphabet_links:
            # self.log("[PAL] " + url)
            yield scrapy.Request(url=url, callback=self.parse_name_list)

    # extract page links of one name letter and make new requests
    def parse_name_list(self, response):
        # extract page number
        if len(response.css('div.list-boxcaptside.list-boxpagenation.group\
         ul li:last-child a::attr(href)')) > 0:
            last_page = int(response.css('div.list-boxcaptside.list-boxpagenation.group\
             ul li:last-child a::attr(href)')[0].re(r'page=(\d+)')[0])
        else:
            last_page = 1
        # crawl name

        for page in range(1, last_page + 1, 1):
            url = response.url + 'page=%d/' % page
            # self.log("[PNL] "+url)
            yield scrapy.Request(url=url, callback=self.parse_star)

    # extract star info and store in database
    def parse_star(self, response):
        stars = response.css('div.d-sect.act-box li a')
        # self.log('[PS] %d'%len(stars))
        query_list = list()
        log_list = list()
        for star in stars:
            id = star.css('::attr(href)').re(r'id=(\d+)')[0]
            img = star.css('img::attr(src)').extract_first()
            link = star.css('::attr(href)').extract_first()
            name1 = star.css('::text').extract_first()
            name2 = star.css('span')[0].css('::text').extract_first()
            videos = star.css('span')[1].css('::text').re(r'(\d+)')[0]
            # self.log('%s %s %s %s \n%s \n%s'%(id,name1,name2,videos,link,img))
            query = "INSERT INTO stars(id,name1,name2,videos,link,img) VALUES(" \
                    + "\'%s\',\'%s\',\'%s\',\'%s\',\'%s\',\'%s\') " % (id, name1, name2, videos, link, img)

            query = query + "ON DUPLICATE KEY UPDATE name1=\'%s\',name2=\'%s\',videos=\'%s\',img=\'%s\'"%(name1, name2, videos, img)
            query_list.append(query)
            log_list.append("%s %s " % (id, name1))

        # insert datum into database
        self.insert_data(query_list, log_list)

    # extract page links of one actress and make new requests
    def parse_video_page(self, response):
        # parse the first page
        video_links = response.css('div.d-item p.tmb a::attr(href)').extract()
        self.parse_video_links(video_links)
        # for video_link in video_links:
        #     # self.log("[PVL] " + video_link)
        #     yield scrapy.Request(url=video_link, callback=self.parse_video)

        # extract extra page links and make new requests
        if len(response.css('div.list-boxcaptside.list-boxpagenation ul li:last-child a::attr(href)')) > 0:
            last_page = int(response.css('div.list-boxcaptside.list-boxpagenation ul li:last-child a::attr(href)').re(
                r'page=(\d+)')[0])
        else:
            last_page = 1

        for page in range(1, last_page + 1, 1):
            if page != 1:
                url = response.url + 'page=%d/' % page
                # self.log("[PVP] " + url)
                yield scrapy.Request(url=url, callback=self.parse_video_list)

    # extract video links and make new requests
    def parse_video_list(self, response):
        video_links = response.css('div.d-item p.tmb a::attr(href)').extract()
        self.parse_video_links(video_links)
        # for video_link in video_links:
        #     # self.log("[PVL] " + video_link)
        #     yield scrapy.Request(url=video_link, callback=self.parse_video)

    # store video link into database not video info
    def parse_video_links(self,url_list):
        query_list = list()
        log_list = list()
        for url in url_list:
            if re.search(r'\/cid=(.+)\/', url):
                cid = re.search(r'\/cid=(.+)\/', url).group(1)
                query = 'INSERT INTO video_links(cid,link) VALUES(\'%s\',\'%s\')'%(cid,url)
                query_list.append(query)
                log_list.append('Link %s '%cid)
                self.insert_data(query_list, log_list)

    # extract video info and store in database
    def parse_video(self, response):
        title = response.css('h1#title ::text').extract_first().replace('\'','"')
        cid = re.search(r'/cid=([\w-]*)/', response.url).group(1)
        favorite = '|'.join(response.css('div.box-rank span.tx-count span::text').re(r'\d+'))
        release = response.css('table.mg-b20 tr')[2].css('td:nth-child(2) ::text').extract_first().strip('\n')
        duration = response.css('table.mg-b20 tr')[3].css('td:nth-child(2) ::text').re(r'(\d+)')[0]
        performer = '|'.join(response.css('span#performer a::attr(href)').re(r'id=(\d+)'))
        director = '|'.join(response.css('table.mg-b20 tr')[5].css('td:nth-child(2) a::attr(href)').re(r'id=(\d+)'))
        series = '|'.join(response.css('table.mg-b20 tr')[6].css('td:nth-child(2) a::attr(href)').re(r'id=(\d+)'))
        maker = '|'.join(response.css('table.mg-b20 tr')[7].css('td:nth-child(2) a::attr(href)').re(r'id=(\d+)'))
        label = '|'.join(response.css('table.mg-b20 tr')[8].css('td:nth-child(2) a::attr(href)').re(r'id=(\d+)'))
        genre = '|'.join(response.css('table.mg-b20 tr')[9].css('td:nth-child(2) a::attr(href)').re(r'id=(\d+)'))
        if len(response.css('p.d-review__average strong::text')) >0:
            rate = response.css('p.d-review__average strong::text').re(r'\d*\.?\d*')[0]
        else:
            rate = 0
        rate_num = response.css('p.d-review__evaluates strong::text').extract_first()
        if len(response.css('p.d-review__evaluates ::text')) >0:
            reviews = response.css('p.d-review__evaluates ::text').re(r'(\d+)')[1]
        else:
            reviews = 0

        img = self.find_img_src(response.css('img.tdmm ::attr(src)').extract_first())

        # print 'title: %s' % title
        # print 'cid: %s' % cid
        # print 'favorite: %s' % favorite
        # print 'release: %s' % release
        # print 'duration: %s' % duration
        # print 'performer: %s' % performer
        # print 'director: %s' % director
        # print 'series: %s' % series
        # print 'maker: %s' % maker
        # print 'label: %s' % label
        # print 'genre: %s' % genre
        # print 'rate: %s' % rate
        # print 'rate num %s' % rate_num
        # print 'comments %s' % comments
        # print 'img: %s' % img

        query = "INSERT INTO videos(cid,favorite,release_date,duration,performer,title" \
                ",director,series,maker,label,genre,rate,img,rate_num,reviews) VALUES(\'%s\',\'%s\',\'%s\',\'%s\',\'%s\',\'%s\',\'%s\',\'%s\',\'%s\',\'%s\',\'%s\',\'%s\',\'%s\',\'%s\',\'%s\')"%(cid,\
                favorite,release,duration,performer,title \
                ,director,series,maker,label,genre,rate,img,rate_num,reviews)

        print query
        self.insert_data([query],['[PV] %s %s'%(cid,title)])
        # parse reviewers and reviews
        if reviews != 0:
            request = scrapy.FormRequest("http://www.dmm.co.jp/review/-/list/ajax-list/", callback=self.parse_reviewer, \
                               formdata={'cid': cid, 'page': str(1), 'limit': reviews, 'sort': 'yes_desc'})
            request.meta['cid'] = cid
            yield request

    # store reviewer id, name and review into database
    def parse_reviewer(self,response):
        cid= response.meta['cid']
        query_list = list()
        log_list = list()
        query_list2 = list()
        log_list2 = list()
        reviews = response.css('div.d-review__with-comment li.d-review__unit')

        for review in reviews:
            reviewer = review.css('span.d-review__unit__reviewer a')
            link = reviewer.css('::attr(href)').extract_first()
            id = reviewer.css('::attr(href) ').re(r'\/id=(\d+)\/')[0]
            name =  reviewer.css('::text').extract_first()
            # self.log('[PR] %s %s'%(id,name))
            query = "INSERT INTO reviewers(id,name,link) VALUES(\'%s\',\'%s\',\'%s\')"%(id,name,link)
            query_list.append(query)
            log_list.append('[PR] %s %s'%(id,name))

            title = review.css('span.d-review__unit__title ::text').extract_first()
            content = "|".join(review.css('div.d-review__unit__comment ::text').extract())
            rate = review.css('p:first-child span:first-child ::attr(class)').re(r'(\d)')[0]
            postdate = review.css('span.d-review__unit__postdate ::text').extract_first()[1:]
            service = review.css('span.d-review__unit__service ::text').extract_first()[1:]
            votes = review.css('p.d-review__unit__voted ::text').re(r'(\d+)')[0]
            useful = review.css('p.d-review__unit__voted strong::text').re(r'(\d+)')[0]

            # print title
            # print content
            # print rate
            # print postdate
            # print service
            # print votes
            # print useful

            query2 = "INSERT INTO reviews(cid,id,title,content,rate,postdate,service,votes,useful)"\
                "VALUES(\'%s\',\'%s\',\'%s\',\'%s\',\'%s\',\'%s\',\'%s\',\'%s\',\'%s\')"%(cid,id,\
                    title,content,rate,postdate,service,votes,useful)

            query_list2.append(query2)
            log_list2.append('[PRC] %s %s'%(cid,id))

        # insert reviewer info into data base
        self.insert_data(query_list, log_list)

        # insert reviews into database
        self.insert_data(query_list2, log_list2)

    def insert_data(self, query_list, log_list):
        # connect to database
        db = MySQLdb.connect(host="localhost",  # your host, usually localhost
                             user="root",  # your username
                             passwd="666666",  # your password
                             db="dmm18",  # name of the data base
                             charset='utf8')  #

        cur = db.cursor()

        for i in range(0, len(query_list), 1):
            try:
                # self.log(query_list[i])
                cur.execute(query_list[i])
                db.commit()
                self.log('[INSERT SUCCESS] %s' % log_list[i])
            except (MySQLdb.Error, MySQLdb.Warning) as e:
                db.rollback()
                self.log('[INSERT FAIL] %s' % log_list[i])
                self.log(e)

        db.close()

    def retrieve_links(self, query):
        # connect to database
        db = MySQLdb.connect(host="localhost",  # your host, usually localhost
                             user="root",  # your username
                             passwd="666666",  # your password
                             db="dmm18",  # name of the data base
                             charset='utf8')  #

        cur = db.cursor()
        cur.execute(query)
        links = [row[0] for row in cur.fetchall()]
        self.log('[GRN LINKS] %d' % len(links))
        db.close()
        return links

    # find the src url of large picture
    def find_img_src(self, src):
        if re.search(r'(p[a-z]\.)jpg', src):
            return src.replace(re.search(r'(p[a-z]\.)jpg', src).group(1), 'pl.')
        elif re.search(r'/consumer_game/', src):
            return src.replace('js-', '-')
        elif re.search(r'js\-([0-9]+)\.jpg$', src):
            return src.replace('js-', 'jp-')
        elif re.search(r'ts\-([0-9]+)\.jpg$', src):
            return src.replace('ts-', 'tl-')
        elif re.search(r'(\-[0-9]+\.)jpg$', src):
            return src.replace(re.search(r'(\-[0-9]+\.)jpg$', src).group(1),
                               'jp' + re.search(r'(\-[0-9]+\.)jpg$', src).group(1))
        else:
            return src.replace('-', 'jp-')

    def find_video_src(self, response):
        iframe_src = response.css('*')[2].css('::attr(src)').extract_first()
        if iframe_src!=None:
            yield scrapy.request(url=iframe_src, callable = self.parse_video_src)

    def parse_video_src(self, response):
        js = response.css('*')[0].css('script ::text').extract_first()
        if js!=None:
            param = max(js.split('\n'), key=len)
            param = param.replace('\\', '')
            re.findall(r'bitrate\"\:(\d+),\"src\":\"(http:\/\/[a-zA-Z0-9\.\/_]+)',param)

    def test(self, response):
        self.log('test')