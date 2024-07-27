import numpy as np

from Data.const import *
from Data.object import *
from perlin_noise import PerlinNoise
import pickle


class Chunk:
    __eq = Block(2758, 0, 0, 0)
    __v_update = np.vectorize(lambda x, camera: x.update(camera) if x != None else None)
    __v_draw = np.vectorize(lambda x, screen: x.draw(screen) if x != None else None)
    tree = np.array([
        [np.nan, np.nan, np.nan, 3217, np.nan, np.nan, np.nan],
        [np.nan, 3217, 3217, 3217, 3217, 3217, np.nan],
        [3217, 3217, 3217, 1909, 3217, 3217, 3217],
        [3217, 3217, 3217, 1909, 3217, 3217, 3217],
        [np.nan, np.nan, np.nan, 1909, np.nan, np.nan, np.nan],
        [np.nan, np.nan, np.nan, 1909, np.nan, np.nan, np.nan],
        [np.nan, np.nan, np.nan, 1909, np.nan, np.nan, np.nan]
    ])
    tree = np.rot90(np.flip(tree), k=3)

    def __init__(self, n, type):
        self.n = n
        self.type = type
        self.blocks = None
        self.indice = None

    def load(self, name, seed):
        try:
            self.blocks = np.load(f'save/{name}/chunks/{self.n}.npy', allow_pickle=True)
            self.indice = np.indices(self.blocks.shape)
        except FileNotFoundError:
            self.blocks = np.full(chunk_size, None, dtype=object)
            self.indice = np.indices(self.blocks.shape)
            if self.type == 0:
                self.random(seed)
            elif self.type == 1:
                self.flat()

    def unload(self, name):
        self.save(name)
        self.blocks = None
        self.indice = None

    def destroy(self, i, j):
        if (block := self.blocks[i, j]) != None:
            if block.hardness >= 0:
                self.blocks[i, j] = None
                return block

    def create(self, item, i, j):
        if (block := self.blocks[i, j]) == None:
            self.blocks[i, j] = item.block(self.n, i, j)
        else:
            if block.replaceable:
                self.blocks[i, j] = item.block(self.n, i, j)
                return block.item()

    def __form_block(self, id, i, j):
        self.blocks[i, j] = Block(id, self.n, i, j)

    def form_layer(self, id, i=None, j=None):
        if i == None and j == None:
            i, j = self.indice
        else:
            i = (i, i) if type(i) == int else i
            j = (j, j) if type(j) == int else j
            if i == None:
                i, j = self.indice[..., j[0]:j[1] + 1]
            elif j == None:
                i, j = self.indice[:, i[0]:i[1] + 1]
            else:
                i, j = self.indice[:, i[0]:i[1] + 1, j[0]:j[1] + 1]
        np.vectorize(self.__form_block)(id, i, j)

    def form_structure(self, structure, pos):
        x, y = pos
        for i in range(structure.shape[0]):
            for j in range(structure.shape[1]):
                id = structure[i, j]
                if not np.isnan(id):
                    self.blocks[x + i, y + j] = Block(int(id), self.n, x + i, y + j)

    def __form_base(self):
        self.form_layer(3151, None, (97, chunk_size[1] - 3))
        self.form_layer(1122, None, (chunk_size[1] - 2, chunk_size[1] - 1))
        self.form_layer(1122, None, (0, 1))
        if self.n == edgechunk[0]:
            self.form_layer(1122, (0, 1))
        elif self.n == edgechunk[1]:
            self.form_layer(1122, (chunk_size[0] - 2, chunk_size[0] - 1))

    def form_trees(self):
        hshape = (int(self.tree.shape[0] / 2), self.tree.shape[1])
        for i in range(4, chunk_size[0] - 4, 8):
            if rd.randint(0, 1):
                j = np.where(self.blocks[i] == self.__eq)[0][0]
                space = self.blocks[i - hshape[0]:i + hshape[0] + 1, j - hshape[1]:j][~np.isnan(self.tree)]
                if np.all(np.vectorize(lambda x: x.replaceable if x != None else True)(space)):
                    self.form_structure(self.tree, (i - hshape[0], j - hshape[1]))

    def flat(self):
        self.form_layer(248, None, 64)
        self.form_layer(2758, None, (65, 70))
        self.form_layer(2458, None, (71, 96))
        self.__form_base()

    def random(self, seed):
        noise1 = PerlinNoise(1, seed)
        noise2 = PerlinNoise(1, seed - 100000)
        for i in range(chunk_size[0]):
            j = 63 + round(noise1([i / chunk_size[0]]) * chunk_size[0])
            r = max(min(71 + round(noise2([i / chunk_size[0]]) * chunk_size[0]), j + 12), j + 2)
            self.form_layer(248, i, j - 1)
            self.form_layer(2758, i, (j, r - 1))
            self.form_layer(2458, i, (r, 96))
        self.__form_base()
        self.form_trees()

    def get_blocks(self, start, end):
        return self.blocks[start[0]:end[0] + 1, start[1]:end[1] + 1]

    def save(self, name):
        try:
            np.save(f'save/{name}/chunks/{self.n}.npy', self.blocks)
        except FileNotFoundError:
            os.makedirs(f'save/{name}/chunks', exist_ok=True)
            self.save(name)

    def update(self, camera):
        Chunk.__v_update(self.blocks, camera)

    def draw(self, screen):
        Chunk.__v_draw(self.blocks, screen)


class World:
    __eq = Block(2758, 0, 0, 0)

    def __init__(self, name, type, seed):
        self.name = name
        self.type = type  # 随机 0,平坦 1
        self.seed = seed
        self.chunks = {i: Chunk(i, type) for i in range(edgechunk[0], edgechunk[1] + 1)}
        self.loading = set()

    def update(self, player):
        loading = {i for i in range(max(player.on - 1, edgechunk[0]), min(player.on + 2, edgechunk[1] + 1))}
        self.load(loading - self.loading)
        self.unload(self.loading - loading)
        self.loading = loading
        for i in self.loading:
            self.chunks[i].update(player.camera)

    def load(self, n):
        for i in n:
            if edgechunk[0] <= i <= edgechunk[1]:
                self.chunks[i].load(self.name, self.seed + i * 20242023)

    def unload(self, n):
        for i in n:
            if edgechunk[0] <= i <= edgechunk[1]:
                self.chunks[i].unload(self.name)

    def save(self, player):
        for i in self.loading:
            self.chunks[i].save(self.name)
        with open(f'save/{self.name}/data.json', 'w') as file:
            json.dump({'type': self.type, 'seed': self.seed, 'mode': player.mode}, file)
        with open(f'save/{self.name}/player.pkl', 'wb') as file:
            pickle.dump(player, file)

    def destroy(self, pos):
        n, i, j = self.where(pos)
        x, y = pos
        block = self.chunks[n].destroy(i, j)
        if block != None:
            drop = rd.choices([None, Items(3719)], p)[0]
            ind = block.chain(self.get_blocks((x - 1, y - 1), (x + 1, y + 1)))
            locking = []
            for i in ind:
                n, i, j = self.where((x + i[0], y + i[1]))
                locking.append(self.chunks[n].destroy(i, j).item())
            return block.item(), locking, drop
        return None, [], None

    def create(self, item, pos):
        n, i, j = self.where(pos)
        if item.check(self.get_blocks((pos[0] - 1, pos[1] - 1), (pos[0] + 1, pos[1] + 1))):
            return self.chunks[n].create(item, i, j)

    def where(self, pos):
        x = pos[0]
        n = int(x // chunk_size[0])
        if x >= 0:
            i = x % chunk_size[0]
        else:
            i = (x - edgex[0]) % chunk_size[0]
        return n, int(i), int(edgey[1] - pos[1])

    def born_place(self, x):
        n, i, _ = self.where((x, 0))
        self.loading = {n - 1, n, n + 1}
        self.load(self.loading)
        low = self.chunks[n].blocks[i]
        indice = np.where(low == World.__eq)
        return low[indice[0][0]].pos[1]

    def get_blocks(self, edge1, edge2):
        n1, i1, j1 = self.where(edge1)
        n2, i2, j2 = self.where(edge2)
        j1, j2 = min(j1, j2), max(j1, j2)
        if n1 == n2:
            i1, i2 = min(i1, i2), max(i1, i2)
            return self.chunks[n1].get_blocks((i1, j1), (i2, j2))
        elif n1 > n2:
            n1, n2 = n2, n1
            i1, i2 = i2, i1
        c1 = self.chunks[n1].get_blocks((i1, j1), (chunk_size[0] - 1, j2))
        c2 = self.chunks[n2].get_blocks((0, j1), (i2, j2))
        return np.vstack((c1, c2))

    def draw(self, screen):
        for i in self.loading:
            self.chunks[i].draw(screen)
