"""Fetch every candidate official box-score document (Wayback, cached) and dump extracted text to raw/text/<key>.txt."""
import os, sys, re, json
from pgfetch import wb, HERE
from pgparse import html_to_text
from pdftxt import pdf_text
M = "https://www.mcdonaldsallamerican.com/content/dam/"
J = "http://jordanbrandclassic.com/"
A = J+"wp-content/uploads/archive/"
REG = [
 # key, url, ts, kind
 ("mcd2006_off","http://mcdepk.com/2006allamericangame/mcdboys.html","20120312231322","html"),
 ("mcd2007_off","http://www.mcdepk.com/2007allamericangame/MediaMaterials/07boysscores.htm","20120324060532","html"),
 ("mcd2008_off","http://mcdepk.com/2008allamericangames/mediadocs/gamestats/Boys_Box_score.html","20101217222352","html"),
 ("mcd2009_off","http://mcdepk.com/2009allamericangames/mediadocs/gamestats/2009_boys_BoxScores.pdf","20101217185602","pdf"),
 ("mcd2010_off","http://www.mcdonaldsallamerican.com:80/2010_AAG_mens_results.html","20100405003952","html"),
 ("mcd2010_off_b","http://mcdepk.com/2010allamericangames/stats/MensMcDonalds_AllAmericanGame.html","20101127124221","html"),
 ("mcd2011_off","http://www.mcdonaldsallamerican.com:80/2011/2011_Boys_Game.pdf","20110409080227","pdf"),
 ("mcd2011_off_b","http://www.mcdonaldsallamerican.com:80/2011/mcdb.htm","20110405070346","html"),
 ("mcd2012_off","http://mcdonaldsallamerican.com:80/2012BoysGameResults.pdf","20120417021031","pdf"),
 ("mcd2013_off","http://www.mcdepk.com:80/2013allamericangames/media/BoysGameStats.html","20130407023601","html"),
 ("mcd2014_off","http://epkzone.com/2014allamericangames/media/2014AllAmericanGamesBoxScores.pdf","20140407071914","pdf"),
 ("mcd2015_off","http://www.mcdonaldsallamerican.com/content/aag/en/MediaCenter/2015-game-materials/2015-Results-Boys/_jcr_content/featuredcontent/everything/file.res/2015%20McDonalds%20Boys%20Final%20Box.pdf","20150402125613","pdf"),
 ("mcd2016_off","http://www.mcdonaldsallamerican.com:80/content/aag/en/MediaCenter/2016/2016-game-materials/2016-Boy-Results/_jcr_content/genericpagecontent/everything/file.res/2016%20McDonalds%20Boys%20Book.pdf","20160428225357","pdf"),
 ("mcd2017_off","http://www.mcdonaldsallamerican.com:80/content/aag/en/MediaCenter/2017/2017-game-materials/BoysResults/_jcr_content/featuredcontent/everything/file.res/2017%20McDonalds%20Boys%20Box.pdf","20180404145445","pdf"),
 ("mcd2018_off",M+"aag/AABOYS.pdf","20181003221127","pdf"),
 ("mcd2019_off",M+"aag/2019-boys-game-final-score.pdf","20190405230440","pdf"),
 ("mcd2022_off",M+"aag/2022-boys-game-final-score.pdf","2","pdf"),
 ("mcd2022_off_b",M+"sites/allamerican/Content/Sponsor/MediaCenter/22_MCDAAG_Boys_Final.pdf","20220523074107","pdf"),
 ("mcd2023_off_a",M+"sites/allamerican/Content/HomeContent/2023%20McDAAG%20Box%20Score%20East%20at%20West%2028%20March.pdf","20230329165751","pdf"),
 ("mcd2023_off_b",M+"sites/allamerican/Content/HomeContent/Box%20Score%20East%20at%20West%2029%20March.pdf","20230329180919","pdf"),
 ("mcd2024_off",M+"sites/allamerican/2024-media-resources-files/McDonald%27s%20All%20American%20Boys%20Game%20Box%20Score.pdf","20240403053314","pdf"),
 ("mcd2025_off_a",M+"sites/allamerican/2025-media-resources-/Box%20Score%20West%20at%20East%2002%20April%20Boys.pdf","20250516213210","pdf"),
 ("mcd2025_off_b",M+"sites/allamerican/2025-media-resources-/Box%20Score%20West%20at%20East%2001%20April.pdf","20250516202900","pdf"),
 # Jordan Brand Classic (national / all-american game)
 ("jbc2005_off",J+"wp-content/uploads/archive/05nationalgamejordanclassic.pdf","20150406024706","pdf"),
 ("jbc2006_off",J+"wp-content/uploads/archive/06allamericangame.pdf","20150405204243","pdf"),
 ("jbc2007_off",J+"wp-content/uploads/archive/07allamericangame.pdf","20150406032215","pdf"),
 ("jbc2008_off","http://www.jordanbrandclassic.com:80/Archives/2008-jordan-brand-classic-national-box-score.html","20110305031733","html"),
 ("jbc2009_off",A+"09natbox.pdf","20150405201256","pdf"),
 ("jbc2010_off",A+"10nationalbox.pdf","20150405223156","pdf"),
 ("jbc2011_off",A+"jbc-all-american2011-stats.pdf","20150405231049","pdf"),
 ("jbc2012_off",A+"NationalBoxScore.pdf","20150405200342","pdf"),
 ("jbc2013_off",A+"NationalBoxScore2013.pdf","20160816033647","pdf"),
 ("jbc2013_off_b",A+"jbc_national_finalbox.pdf","20150406000516","pdf"),
 ("jbc2014_off",A+"2014nationalboxscore.pdf","20150406003813","pdf"),
 ("jbc2015_off",J+"wp-content/uploads/2015/03/Box-Score-All-America-Game.pdf","20150501031530","pdf"),
 ("jbc2016_off",J+"wp-content/uploads/2016/01/Jordan-Classic-National-Box-Score.pdf","20161228103814","pdf"),
 ("jbc2017_off",J+"wp-content/uploads/2017/04/2017-Jordan-Brand-Classic-National-Boys-Game.pdf","20170420150506","pdf"),
 ("jbc2018_off","https://jordanbrandclassic.com/wp-content/uploads/2018/04/2018JBCBoysFinalBox.pdf","20180508185136","pdf"),
 ("jbc2019_off","https://jordanbrandclassic.com/wp-content/uploads/2019/04/Boys-Game.pdf","20221207031941","pdf"),
 ("jbc2022_off","https://jordanbrandclassic.com/wp-content/uploads/2022/04/Boys-Jordan-Game-4-15-22.pdf","20220516163000","pdf"),
 ("hs2018_off","http://www.nikehoopsummit.com:80/images/18%20hsum%20box%20score.pdf","20180517093340","pdf"),
]
def run(keys=None):
    os.makedirs(os.path.join(HERE, "raw", "text"), exist_ok=True)
    out = {}
    for key, url, ts, kind in REG:
        if keys and key not in keys: continue
        tp = os.path.join(HERE, "raw", "text", key + ".txt")
        if os.path.exists(tp):
            out[key] = "cached"; continue
        d = wb(url, ts, binary=(kind == "pdf"))
        if d is None:
            out[key] = "MISSING"; continue
        try:
            txt = pdf_text(d) if kind == "pdf" else html_to_text(d)
        except Exception as e:
            out[key] = "ERR " + repr(e)[:80]; continue
        open(tp, "w").write(txt)
        out[key] = "ok %d" % len(txt)
    return out
if __name__ == "__main__":
    for k, v in run(sys.argv[1:] or None).items(): print(k, v)
