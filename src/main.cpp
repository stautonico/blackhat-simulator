//#include <blackhat/computer.h>
//
//int main() {
//
//    Blackhat::Computer c;
//    c.start();
//
//    return 0;
//}


#include <cereal/archives/json.hpp>
#include <cereal/types/map.hpp>

#include <map>
#include <sstream>
#include <memory>

class Inode {
public:
    Inode() = default;

    Inode(std::string name, std::string content) {
        m_name = name;
        m_content = content;
    }

    std::string get_name() { return m_name; }

    std::string read() { return m_content; }

    void write(std::string content) { m_content = content; }


    template<class Archive>
    void serialize(Archive &archive) {
        archive(m_name, m_content);
    }

private:
    std::string m_name;
    std::string m_content;
};

class Folder {
public:
    std::shared_ptr<Inode> get_child(std::string name) {
        auto it = m_children.find(name);

        if (it == m_children.end()) {
            return nullptr;
        } else {
            return it->second;
        }
    }

    void add_child(Inode *inode) {
        m_children[inode->get_name()] = std::unique_ptr<Inode>(inode);
    }

    template<class Archive>
    void serialize(Archive &archive) {
        archive(m_children);

        archive.serializeDeferments();
    }


private:
    std::map<std::string, std::shared_ptr<Inode>> m_children;
};

#include <iostream>

int main() {
    std::stringstream ss; // any stream can be used

    {
        Folder f;

        auto i1 = new Inode("inode 1", "inode 1's content");
        auto i2 = new Inode("inode 2", "inode 2's content");
        auto i3 = new Inode("inode 3", "inode 3's content");

        f.add_child(i1);
        f.add_child(i2);
        f.add_child(i3);


        cereal::JSONOutputArchive oarchive(ss); // Create an output archive



        oarchive(f);
    }

    std::cout << ss.str() << std::endl;

    {
        cereal::JSONInputArchive iarchive(ss);

        Inode in1, in2, in3;
        iarchive(in1, in2, in3);

        std::cout << in1.get_name() << std::endl;
        std::cout << in1.read() << std::endl;
        std::cout << in2.get_name() << std::endl;
        std::cout << in2.read() << std::endl;
        std::cout << in3.get_name() << std::endl;
        std::cout << in3.read() << std::endl;

    }
}