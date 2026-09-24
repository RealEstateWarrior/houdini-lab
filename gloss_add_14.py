# -*- coding: utf-8 -*-
"""用語を足す（その14: 実践「夕暮れの海」の作り直しで出てきた言葉）。"""

ADD = {
    "simulation": [
        {"term": "波の設計図 / Ocean Spectrum", "reading": "なみのせっけいず",
         "def": "海の波を「どの長さの波が、どれだけの高さで、どちらへ進むか」の混ざり方で表したもの。oceanspectrum で風の強さと向きから作り、"
                "oceanevaluate が点をその通りに動かす。シミュレーションしなくても海が作れる。"},
        {"term": "うねり / Swell", "reading": "うねり",
         "def": "遠くの風で生まれて、長い距離を旅してきた、長くなだらかな波。沖の海は、うねりの上に、その場の風の波とさざ波が乗っている。"
                "実践「夕暮れの海」では、Grid Size 300 m の設計図をうねり、37 m を風の波、4.3 m をさざ波にして重ねた。"},
    ],
    "render": [
        {"term": "光の道 / Sun Glitter", "reading": "ひかりのみち",
         "def": "低い太陽や月の下の水面に、縦に伸びて見える光の帯。細かい波の 1 つ 1 つが太陽を映した点の集まり。"
                "Karma では、水の材質の Roughness をほぼ 0（実践「夕暮れの海」では 0.015）にし、足もとの点を細かくしてさざ波を作ると出る。"
                "Roughness を上げると太い白い帯になり（0.02→0.15 で幅 4 倍）、さざ波を高くすると粒のまま広がる（実験218）。"},
        {"term": "Far Clipping", "reading": "ファークリッピング",
         "def": "カメラが写す一番遠い距離。cam の既定は 10000（m）で、それより遠い物は写らずに透明になる。半径 20 km の空の球で包む場面では、1,000,000 などに上げておく（実践「夕暮れの海」）。"},
    ],
}

ADD["simulation"].append(
    {"term": "砕波（さいは）/ Breaking Wave", "reading": "さいは",
     "def": "沖から来た波が浅い所で高く切り立ち、崩れて白い泡になること。砂浜では、崩れる所から岸までが白い泡の帯になる。"
            "実践「冬の朝の七里ヶ浜」では、シミュレーションせずに、attribwrangle で「岸へ進む波の列」を足し、崩れる所（沖 27〜41 m）から岸までに泡の色を付けた。"})
ADD["render"].append(
    {"term": "Render Visibility", "reading": "レンダービジビリティ",
     "def": "オブジェクトを、カメラ・影・映り込みなどのどれに写すかを決める、Geometry オブジェクトのつまみ（vm_rendervisibility）。"
            "実践「冬の朝の七里ヶ浜」では、空の球に「-shadow」を入れても、Karma で平行光の影は消えなかった（空の内側に円い光を置いて解決）。"})
ADD["render"].append(
    {"term": "円い光 / Disk Light", "reading": "まるいひかり",
     "def": "hlight の Light Type を disk にした、円い面から出る光。遠くに見かけ 0.54° の大きさで置くと、太陽の代わりになり、水面のきらめきにも丸い太陽として映る。"
            "Normalize Light Intensity to Area を切ると、Intensity がそのまま面の明るさになる（実践「冬の朝の七里ヶ浜」では 150,000）。"})

ADD["houdini"] = ADD.get("houdini", []) + [
    {"term": "revertToDefaults()", "reading": "リバートトゥデフォルツ",
     "def": "Python（hou）で、つまみを既定値に戻す関数。戻る先は「つまみの既定値」で、ノードを作った直後の値とは限らない。"
            "pyrosolver の Use Control Field は、作った直後は「入り」なのに、revertToDefaults では「切り」に戻った（実験220）。"
            "作った直後の値に戻したいときは、その値を直接 set する。"}]

ADD["render"].append(
    {"term": "usdinstancerpath", "reading": "ユーエスディーインスタンサーパス",
     "def": "パックした形に付ける文字の属性。USD に渡すとき、この名前のポイントインスタンサーにまとめる目印になる。"
            "ただし /obj の Karma で草 3 万本を撮ると、付けても付けなくても時間は同じだった（86 秒と 89 秒）。"
            "Solaris の sopimport で Packed Primitives を Create Point Instancer にすると 6.7 秒で撮れた（実験222）。"})

ADD["simulation"].append(
    {"term": "白波 / Whitecap", "reading": "しろなみ",
     "def": "沖で風に押された波の頭が崩れて、白く泡立つもの。本物の海で白波が覆う割合は、風速の 3.4 乗にほぼ比例する（Monahan らの式）。"
            "風 5 m/秒で 0.09%、10 m/秒で 1%、15 m/秒で 4%。oceanevaluate の cusp で色を付けるときのしきい値は、実験223 の表で決められる。"})

ADD["render"].append(
    {"term": "Time Samples（モーションブラー）", "reading": "タイムサンプルズ",
     "def": "Karma がシャッターの開いている間に、物の位置や形を何回調べるか。オブジェクトの動きは Transform Time Samples、形の変化は Geometry Time Samples（どちらも既定 2）。"
            "2 回だと、その間をまっすぐ結ぶので、速く回る物のブレが弧ではなく直線になる。オブジェクトの回転は既定の Rotation Blur で弧になるが、"
            "SOP で回すと Geometry Time Samples を 8 にしてやっと弧になった（90° 回る場合。実験230）。"})

ADD["render"].append(
    {"term": "Diffuse Limit", "reading": "ディフューズリミット",
     "def": "Karma が、光がざらざらした面（壁・床など）で跳ね返るのを何回まで追うか。既定 1。"
            "窓の光だけで照らす明るい部屋では、1 だと本来の明るさの 72%、4 で 91%、8 で 98% になった。時間は 1 → 4 で 2 倍（実験234）。"})

ADD["render"].append(
    {"term": "Volume Limit", "reading": "ボリュームリミット",
     "def": "Karma が、煙や雲の中で光が散らばるのを何回まで追うか。既定 0。雲では上げるほど明るくなり、16 でもまだ落ち着かなかった。"
            "時間は 0 で 13 秒、16 で 378 秒（640×360・32 サンプル）。上げると白く飛ぶので、日差しを弱めて合わせる（実験235）。"})

ADD["render"].append(
    {"term": "Refraction Limit", "reading": "リフラクションリミット",
     "def": "Karma が、光が透明な物の境目を通り抜けて曲がるのを何回まで追うか。既定 4。追うのをやめた所は黒くなる。"
            "氷の入ったグラスの水では、4 だと氷の奥が黒く残り、8 で透明になった（実験236）。"})

ADD["render"].append(
    {"term": "Color Limit", "reading": "カラーリミット",
     "def": "Karma が、1 つのサンプルの明るさをどこで切り詰めるか。既定 10。ぽつぽつと白く光る点（ファイアフライ）を抑える。"
            "水面に映る太陽の光の道では、1000 に上げると明るさが 6.8 倍になり、16 サンプルのざらつきも 28.5% → 201% に増えた（実験238）。"})
ADD["render"].append(
    {"term": "ファイアフライ / Firefly", "reading": "ファイアフライ",
     "def": "レンダーした画に、ぽつぽつと出る白く明るい点。とても明るい光（太陽の映り込みなど）を、少ないサンプルでたまたま拾った画素が光る。"
            "Color Limit で明るさを切り詰めるか、サンプルを増やすか、ノイズ除去で抑える（実験238）。"})

ADD["render"].append(
    {"term": "ノイズ除去 / Denoiser（OIDN・OptiX）", "reading": "ノイズじょきょ",
     "def": "少ないサンプルで撮ったざらざらの画を、なめらかに整える仕上げ。Karma の Denoiser で Intel OIDN か NVIDIA OptiX を選ぶ。"
            "ドーナツ・雪だるまでは、4 サンプル＋ノイズ除去で 32 サンプル（なし）と同じくらい 512 サンプルの画に近く、OptiX がわずかに近かった。"
            "かかる時間は 1 秒未満（実験241）。"})

ADD["render"].append(
    {"term": "MaterialX（mtlxstandard_surface）", "reading": "マテリアルエックス",
     "def": "いろいろなソフトやレンダラーで共通に使える材質の書き方。Houdini では /mat に mtlxstandard_surface などの箱を置いて作る。"
            "Karma XPU では、形に点の色 Cd があると principledshader の色が Cd に置き換わったが、MaterialX の材質は CPU と同じ色で写った（実験243）。"})

ADD["simulation"].append(
    {"term": "Dissipation（Pyro）", "reading": "ディシペーション",
     "def": "pyrosolver で、煙の濃さ（density）が時間とともに薄れて消える速さ。既定 0.1。出る量と釣り合うと、煙の量は Dissipation にほぼ反比例した（倍にすると半分）。"
            "火元が density を出していない（Source Burn だけの）焚き火では、変えても何も変わらなかった（実験244）。"})
