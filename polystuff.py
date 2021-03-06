import pandas as pd
import polyline as pl
from collections import defaultdict
import math

epsilon = 0.0001

class PointList:
    def __init__(self):
        self.coord = []
        self.accm = []
        self.cntr = []
        # self.type = []
        self.numPoints = 0
        self.dict = defaultdict(lambda: defaultdict(list))

    def addlist(self, point, weight=1):
        closest = -1
        ix = int(point[0] * 1000)
        iy = int(point[1] * 1000)
        for i in self.dict[ix][iy]:
            dx = abs(self.coord[i][0] - point[0]) + abs(self.coord[i][1] - point[1])
            if dx < epsilon:
                closest = i
                self.accm[i][0] += point[0] * weight
                self.accm[i][1] += point[1] * weight
                self.cntr[i] += weight
                self.coord[i][0] = self.accm[i][0] / self.cntr[i]
                self.coord[i][1] = self.accm[i][1] / self.cntr[i]
                break
        if closest == -1:
            self.dict[ix][iy].append(self.numPoints)
            self.coord.append([point[0], point[1]])
            self.accm.append([point[0] * weight, point[1] * weight])
            self.cntr.append(weight)
            # self.type.append(type)
            closest = self.numPoints
            self.numPoints += 1
        return closest

    def findpoint(self, point):
        closest = -1
        ix = int(point[0] * 1000)
        iy = int(point[1] * 1000)
        for i in self.dict[ix][iy]:
            dx = abs(self.coord[i][0] - point[0]) + abs(self.coord[i][1] - point[1])
            if dx < epsilon and self.cntr[i] > 4:
                closest = i
                break
        return closest

    def getlinepoints(self, my_list, l, r, epsi=0.0001):
        if l[0] == r[0] and l[1] == r[1]:
            c = self.findpoint(l)
            if c != -1:
                my_list.append(c)
            return
        lx = int(l[0] * 1000)
        ly = int(l[1] * 1000)
        rx = int(r[0] * 1000)
        ry = int(r[1] * 1000)
        x1 = min(lx, rx)
        x2 = max(lx, rx)
        y1 = min(ly, ry)
        y2 = max(ly, ry)
        xx = l[0]
        yy = l[1]

        vx = r[0] - l[0]
        vy = r[1] - l[1]

        la = vy
        lb = -vx
        nrm = math.sqrt(la * la + lb * lb)
        la /= nrm
        lb /= nrm
        lc = -la * xx - lb * yy

        templist = []
        for x in range(x1, x2 + 1):
            for y in range(y1, y2 + 1):
                for i in self.dict[x][y]:
                    d = abs(la * self.coord[i][0] + lb * self.coord[i][1] + lc)
                    if d > epsi:
                        continue
                    px = self.coord[i][0] - l[0]
                    py = self.coord[i][1] - l[1]

                    pos = px * -lb + py * la

                    if 0.0 <= pos <= nrm:
                        templist.append([i, pos])
        templist = sorted(templist, key=lambda k: k[1])

        for x in templist:
            my_list.append(x[0])

# "../data/train.csv/train.csv"
# "../data/test_additional.csv"
# "../data/validation.csv"
def process_road(name_train, name_test, name_val, points_from_csv = True):
    df_train = pd.read_csv(name_train)
    #df_train = pd.read_csv("../data/test_additional.csv")
    df_test = pd.read_csv(name_test)
    df_val = pd.read_csv(name_val)

    cities = set()

    def citylist_from_df(_df):
        citylist = defaultdict(list)

        ROWS = len(_df)

        for i in range(ROWS):
            if (i % 1000 == 0):
                print(i//1000)
            cities.add(city)
            rw = _df.iloc[i]
            city = rw.main_id_locality
            citylist[city].append(i)

        print("built citylist")
        return citylist

    citylist = citylist_from_df(df_train)
    citylist_test = citylist_from_df(df_test)
    citylist_val = citylist_from_df(df_val)

    process_list = [
        [ df_train, citylist ],
        [ df_test, citylist_test ],
        [ df_val, citylist_val ],
    ]

    for city in cities:
        plst = PointList()

        print("Processing city", city)

        if points_from_csv:
            pdf = pd.read_csv("points{}.csv".format(city))
            n = len(pdf)

            for r in range(n):
                xy = [pdf.iloc[r].x, pdf.iloc[r].y]
                if (r % 10000 == 0):
                    print(xy)
                plst.addlist(xy, 5)
            print("Read point.csv")
        else:
            count = 0
            for i in citylist[city]:
                count += 1
                if (count % 1000 == 0):
                    print(count // 1000, plst.numPoints)
                try:
                    dat = pl.decode(df_train.iloc[i].route)
                except TypeError:
                    print("invalid route", i)
                    continue
                numPoints = len(dat)
                for j in range(0, numPoints):
                    if j == 0 or j == numPoints - 1:
                        continue
                    doadd = 1
                    dx1 = -dat[j - 1][0] + dat[j][0]
                    dy1 = -dat[j - 1][1] + dat[j][1]
                    dx2 = dat[j + 1][0] - dat[j][0]
                    dy2 = dat[j + 1][1] - dat[j][1]
                    sn = dx1 * dx2 + dy1 * dy2
                    d1 = math.sqrt(dx1 * dx1 + dy1 * dy1)
                    d2 = math.sqrt(dx2 * dx2 + dy2 * dy2)
                    if d1 != 0.0 and d2 != 0.0:
                        sn /= d1 * d2
                        if sn >= 0.8:
                            doadd = 0
                    if doadd:
                        plst.addlist(dat[j])

            pdf = pd.DataFrame(columns=['x', 'y'])

            for i in range(plst.numPoints):
                if plst.cntr[i] > 4:
                    pdf.loc[len(pdf)] = [plst.coord[i][0], plst.coord[i][1]]

            print("Generated points")

            pdf.to_csv("points{}.csv".format(city), index=False)

        numRoutes = len(citylist[city])

        nbr = []
        for i in range(plst.numPoints):
            nbr.append(set())

        ncnt = [0] * plst.numPoints

        for i in range(numRoutes):
            if i % 1000 == 0:
                print(i // 1000)
            ix = citylist[city][i]
            try:
                dat = pl.decode(df_train.iloc[ix].route)
            except TypeError:
                continue
            newRoute = []
            numPoints = len(dat)
            for j in range(0, numPoints):
                # if j == 0 or j == numPoints-1:
                #    newRoute.append(j)
                if j != 0:
                    plst.getlinepoints(newRoute, dat[j - 1], dat[j])
            l = len(newRoute)
            prev = -1
            for j in range(l):
                if (prev == newRoute[j]):
                    continue
                if prev != -1:
                    ncnt[prev] += 1
                    nbr[prev].add(newRoute[j])
                    nbr[newRoute[j]].add(prev)
                prev = newRoute[j]
            ncnt[prev] += 1

        print("Processed city")

        pid = 0

        for pr in process_list:
            _df = pr[0]
            _cl = pr[1]

            csvdict = []

            numRoutes = len(_cl[city])

            print(numRoutes)

            for i in range(numRoutes):
                if i % 1000 == 0:
                    print(i // 1000)
                ix = _cl[city][i]
                Id = _df.iloc[ix].Id
                try:
                    dat = pl.decode(_df.iloc[ix].route)
                except TypeError:
                    continue
                newRoute = []
                numPoints = len(dat)
                off = 0.0001
                prev = -1
                for j in range(0, numPoints):
                    if j != 0:
                        plst.getlinepoints(newRoute, dat[j - 1], dat[j])
                l = len(newRoute)
                prev = -1
                f = 0
                pc200 = 0
                pc500 = 0
                pc1000 = 0
                for j in range(l):
                    if (prev == newRoute[j]):
                        continue
                    if len(nbr[prev]) > 2:
                        if ncnt[prev] >= 200:
                            pc200 += 1
                        if ncnt[prev] >= 500:
                            pc500 += 1
                        if ncnt[prev] >= 1000:
                            pc1000 += 1
                    prev = newRoute[j]
                if len(nbr[prev]) > 2:
                    if ncnt[prev] >= 200:
                        pc200 += 1
                    if ncnt[prev] >= 500:
                        pc500 += 1
                    if ncnt[prev] >= 1000:
                        pc1000 += 1
                csvdict.append({"id": Id, "p200": pc200, "p500": pc500, "p1000": pc1000})

            pdf = pd.DataFrame(csvdict)
            pdf.to_csv("pr{}_{}.csv".format(pid, city), index=False)

            pid += 1

            print("Done {} {}".format(pid, city))



# "../data/train.csv/train.csv"
# "../data/test_additional.csv"
# "../data/validation.csv"
process_road("../data/train.csv/train.csv", "../data/text_additional.csv", "../data/validation.csv")
